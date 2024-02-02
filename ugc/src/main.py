import os
import httpx

from http import HTTPStatus

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.exceptions import AuthJWTException
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status, HTTPException
from fastapi.responses import ORJSONResponse

from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from core.config import auth_jwt_settings, settings, mongo_settings
from services.tracer import configure_tracer

from storage import mq, nosql
from storage.mq import KafkaProducer
from core.logger import logger

from api.v1 import events, interactions


@AuthJWT.load_config
def get_config():
    return auth_jwt_settings


@asynccontextmanager
async def lifespan(application: FastAPI):
    # init kafka
    mq.queue_producer = KafkaProducer(bootstrap_servers='kafka-node1:9092')
    nosql.nosql = nosql.MongoDBConnector(db_name=mongo_settings.db,
                                         collection_name=mongo_settings.collection,
                                         hosts=mongo_settings.hosts)
    await mq.queue_producer.start()

    yield

    nosql.nosql.client.close()
    await mq.queue_producer.stop()


app = FastAPI(
    title=settings.project_name,
    docs_url="/api/v1/openapi",
    openapi_url="/api/v1/openapi.json",
    root_path="/api/",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
)


@app.get("/api/v1/health")
async def healthcheck():
    logger.info("healthcheck ok")
    return {"status": "ok"}


trace_excluded_endpoints = [app.url_path_for("healthcheck")]


@app.middleware("http")
async def auth_user(request: Request, call_next):
    if request.method == "POST":
        async with httpx.AsyncClient() as client:
            auth = await client.get(
                f'''{os.getenv("AUTH_API_URL", "http://127.0.0.1/auth/api/v1/")}users/my_user''',
                headers={
                    "X-Request-Id": request.headers.get("X-Request-Id"),
                    "Cookie": request.headers.get("Cookie"),
                })
        if auth.status_code != HTTPStatus.OK:
            raise HTTPException(status_code=HTTPStatus.UNAUTHORIZED, detail="Token invalid!")
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


if settings.jaeger_enabled:
    configure_tracer()
    FastAPIInstrumentor.instrument_app(app, excluded_urls=",".join(trace_excluded_endpoints))


app.include_router(events.router, prefix="/api/v1/events")
app.include_router(interactions.router, prefix="/api/v1/interactions")
