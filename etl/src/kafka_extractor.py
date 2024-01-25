import logging
from collections.abc import Generator

import backoff
from kafka import KafkaConsumer, TopicPartition
from kafka.consumer.fetcher import ConsumerRecord

from config import KafkaSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KafkaExtractor:
    def __init__(self, config: KafkaSettings) -> None:
        self.config = config
        self.consumer = self.connect()

    @backoff.on_exception(backoff.expo, Exception)
    def connect(self) -> KafkaConsumer:
        return KafkaConsumer(
            bootstrap_servers=self.config.bootstrap_servers,
            auto_offset_reset=self.config.auto_offset_reset,
            group_id=self.config.group_id,
            enable_auto_commit=False,
            consumer_timeout_ms=1000,
        )

    def extract(self, from_timestamp: int = 0) -> Generator[ConsumerRecord, None, None]:
        self.consumer.subscribe([self.config.views_topic])
        self.consumer.poll(0)

        # Get the list of partitions assigned
        partitions = self.consumer.assignment()

        # Convert timestamp to offset for each partition
        for partition in partitions:
            topic_partition = TopicPartition(partition.topic, partition.partition)

            # Get the offset for the given timestamp with delta to next entrie
            offsets = self.consumer.offsets_for_times({topic_partition: from_timestamp + 1})

            if offsets and topic_partition in offsets and offsets[topic_partition] is not None:
                offset = offsets[topic_partition].offset
                self.consumer.seek(topic_partition, offset)
            else:
                return

        try:
            yield from self.consumer
        except Exception as e:
            logger.error("Error while reading messages from Kafka: %s", e)
        finally:
            self.consumer.unsubscribe()
