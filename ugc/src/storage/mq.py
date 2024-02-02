from typing import Type

from aiokafka import AIOKafkaProducer
from abc import ABC, abstractmethod


class QueueProducer(ABC):
    @abstractmethod
    async def send_view(self, *args, **kwargs):
        pass


class KafkaProducer(AIOKafkaProducer, QueueProducer):
    async def send_view(self, user_id, film_id, value):
        await self.send(topic="views", value=str.encode(value), key=str.encode(f"{user_id}:{film_id}"))
        return True

    async def send_event(self, user_id, film_id, value, event_type):
        await self.send(topic="events", value=str.encode(value), key=str.encode(f"{user_id}:{film_id}:{event_type}"))
        return True


queue_producer = KafkaProducer


async def get_producer() -> Type[KafkaProducer]:
    return queue_producer
