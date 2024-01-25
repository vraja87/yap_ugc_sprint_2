import logging
import time

import backoff
import redis

from clickhouse_loader import ClickHouseLoader
from config import config
from kafka_extractor import KafkaExtractor
from transformer import KafkaToClickHouseDataTransformer

logging.basicConfig(level=logging.INFO)


class ETL:
    def __init__(self) -> None:
        self.extractor = KafkaExtractor(config.kafka)
        self.transformer = KafkaToClickHouseDataTransformer()
        self.loader = ClickHouseLoader(config.clickhouse)
        self.batch_size = config.batch_size
        self.sleep_seconds = config.sleep_seconds

    @backoff.on_exception(backoff.expo, Exception)
    def save_last_processed_timestamp(self, timestamp: int = 0) -> None:
        redis_client = redis.StrictRedis(host=config.redis.host, port=config.redis.port, db=config.redis.db)
        redis_client.set("last_processed_timestamp", timestamp)

    @backoff.on_exception(backoff.expo, Exception)
    def get_last_processed_timestamp(self) -> int:
        redis_client = redis.StrictRedis(host=config.redis.host, port=config.redis.port, db=config.redis.db)
        last_processed_timestamp = redis_client.get("last_processed_timestamp")
        return int(last_processed_timestamp) if last_processed_timestamp else 0  # type: ignore[arg-type]

    def start(self) -> None:
        try:
            while True:
                last_processed_timestamp = self.get_last_processed_timestamp()
                logging.info(f"Start ETL from last processed timestamp: {last_processed_timestamp}")

                for message in self.extractor.extract(from_timestamp=last_processed_timestamp):
                    transformed_data = self.transformer.transform(message)
                    if transformed_data:
                        # TODO: it should be a batch in production
                        self.loader.load(transformed_data)

                    # Save last processed timestamp event if broken message
                    self.save_last_processed_timestamp(message.timestamp)
                time.sleep(self.sleep_seconds)
        except Exception as e:
            logging.exception(f"ETL process stopped with error: {e}")
        finally:
            logging.exception("ETL process completed")


if __name__ == "__main__":
    etl_process = ETL()
    etl_process.start()
