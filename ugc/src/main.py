import logging

from http import HTTPStatus

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from fastapi import Depends

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from core.config import auth_jwt_settings, settings
from services.tracer import configure_tracer

from storage import mq
from storage.mq import KafkaProducer, QueueProducer, get_producer

from models.kafka import ViewMessage, EventMessage


@AuthJWT.load_config
def get_config():
    return auth_jwt_settings


@asynccontextmanager
async def lifespan(application: FastAPI):
    # init kafka
    mq.queue_producer = KafkaProducer(bootstrap_servers='kafka-node1:9092')
    await mq.queue_producer.start()

    yield

    await mq.queue_producer.stop()


app = FastAPI(
    title=settings.project_name,
    docs_url="/api/v1/openapi",
    openapi_url="/api/v1/openapi.json",
    root_path="/",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


@app.get("/api/v1/health")
async def healthcheck():
    return {"status": "ok"}


trace_excluded_endpoints = [app.url_path_for("healthcheck")]


@app.middleware("http")
async def trace_request(request: Request, call_next):
    if settings.jaeger_enabled and request.scope["path"] not in trace_excluded_endpoints:
        request_id = request.headers.get("X-Request-Id")
        if not request_id:
            return ORJSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST, content={"detail": "X-Request-Id is required"}
            )
        tracer = trace.get_tracer(__name__)
        with tracer.start_as_current_span(request.url.path) as span:
            span.set_attribute("http.request_id", request_id)
            response = await call_next(request)
            return response
    else:
        response = await call_next(request)
        return response


@app.middleware("http")
async def auth_user(request: Request, call_next):
    auth = AuthJWT(request)
    if request.scope["path"] != "/api/v1/health":
        token = request.headers.get("Cookie")
        if token and "access_token" in token:
            try:
                await auth.jwt_required()
                request.state.user_id = await auth.get_jwt_subject()
            except AuthJWTException:
                return ORJSONResponse(
                    status_code=HTTPStatus.UNAUTHORIZED, content={"detail": "Token invalid!"}
                )
        else:
            return ORJSONResponse(
                status_code=HTTPStatus.UNAUTHORIZED, content={"detail": "Token not provided!"}
            )
    response = await call_next(request)
    return response


if settings.jaeger_enabled:
    configure_tracer()
    FastAPIInstrumentor.instrument_app(app, excluded_urls=",".join(trace_excluded_endpoints))


@app.post(
    "/api/write_user_view",
    summary="Load view messages into MQ",
    status_code=HTTPStatus.CREATED,
    description="Sends views info in warehouse/mq",
)
async def load_view_in_mq(
    request: Request,
    msg: ViewMessage,
    queue_producer: QueueProducer = Depends(get_producer),
):
    await queue_producer.send_view(
        value=msg.value,
        film_id=msg.film_id,
        user_id=request.state.user_id,
    )


@app.post(
    "/api/write_user_event",
    summary="Load event messages into MQ",
    status_code=HTTPStatus.CREATED,
    description="Sends events info in warehouse/mq",
)
async def load_event_in_mq(
    request: Request,
    msg: EventMessage,
    queue_producer: QueueProducer = Depends(get_producer),
):
    await queue_producer.send_event(
        value=msg.value,
        film_id=msg.film_id,
        user_id=request.state.user_id,
        event_type=msg.event_type,
    )
