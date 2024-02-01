from pydantic import Field
from pydantic_settings import BaseSettings

VIEWS_TOPIC = "views"
EVENTS_TOPIC = "events"


class KafkaSettings(BaseSettings):
    bootstrap_servers: str = Field("kafka-node1:9092", env="KAFKA_BOOTSTRAP_SERVERS")  # type: ignore[call-arg]
    auto_offset_reset: str = "earliest"
    group_id: str = "echo-messages-to-stdout"
    views_topic: str = VIEWS_TOPIC
    events_topic: str = EVENTS_TOPIC
    enable_auto_commit: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class ClickHouseSettings(BaseSettings):
    host: str = Field("clickhouse-node1", env="CLICKHOUSE_HOST")  # type: ignore[call-arg]
    port: int = 9000
    cluster: str = Field("company_cluster", env="CLICKHOUSE_CLUSTER")  # type: ignore[call-arg]
    database: str = Field("shard", env="CLICKHOUSE_DATABASE")  # type: ignore[call-arg]
    user: str = Field("admin", env="CLICKHOUSE_USER")  # type: ignore[call-arg]
    password: str = Field("qwerty", env="CLICKHOUSE_PASSWORD")  # type: ignore[call-arg]

    views_table_name: str = VIEWS_TOPIC
    custom_events_table_name: str = EVENTS_TOPIC

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


class RedisSettings(BaseSettings):
    host: str = Field("redis", env="REDIS_HOST")  # type: ignore[call-arg]
    port: int = 6379
    db: int = 0


class ETLConfig(BaseSettings):
    kafka: KafkaSettings
    clickhouse: ClickHouseSettings
    redis: RedisSettings

    batch_size: int = 100
    sleep_seconds: int = 5


clickhouse_settings = ClickHouseSettings()  # type: ignore[call-arg]
kafka_settings = KafkaSettings()  # type: ignore[call-arg]
redis_settings = RedisSettings()  # type: ignore[call-arg]

config = ETLConfig(kafka=kafka_settings, clickhouse=clickhouse_settings, redis=redis_settings)
