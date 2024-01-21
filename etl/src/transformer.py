import logging
from datetime import datetime
from uuid import UUID

from kafka.consumer.fetcher import ConsumerRecord
from pydantic import BaseModel


class FilmViewEventDTO(BaseModel):
    user_id: UUID
    film_id: UUID
    number_seconds_viewing: int
    record_time: datetime


class KafkaToClickHouseDataTransformer:
    def transform(self, message: ConsumerRecord) -> FilmViewEventDTO | None:
        result = None
        try:
            if message.key is None:
                logging.warning("Key is None. Skipping transformation.")
                return None

            key_str = message.key.decode("utf-8")
            user_id, film_id = key_str.split(":")
            number_seconds_viewing = int(message.value)
            record_time = datetime.fromtimestamp(message.timestamp / 1000)
            result = FilmViewEventDTO(
                user_id=user_id, film_id=film_id, number_seconds_viewing=number_seconds_viewing, record_time=record_time
            )
        except ValueError as ve:
            logging.error(f"ValueError during transformation: {ve}")
        except Exception as e:
            logging.exception(f"Error during transformation: {e}")
        return result
