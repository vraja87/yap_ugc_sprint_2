from http import HTTPStatus

from fastapi import APIRouter, Depends, Request
from storage.mq import QueueProducer, get_producer

from models.kafka import ViewMessage, EventMessage


router = APIRouter()


@router.post(
    "/write_user_view",
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


@router.post(
    "/write_user_event",
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
