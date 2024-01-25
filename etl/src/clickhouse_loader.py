import logging

import backoff
from clickhouse_driver import Client

from config import ClickHouseSettings
from transformer import FilmViewEventDTO


class ClickHouseLoader:
    def __init__(self, config: ClickHouseSettings) -> None:
        self.config = config
        self.client = self.connect()
        self.init_database_and_tables()

    @backoff.on_exception(backoff.expo, Exception)
    def connect(self) -> Client:
        return Client(host=self.config.host, port=self.config.port)

    @backoff.on_exception(backoff.expo, Exception)
    def init_database_and_tables(self) -> None:
        cluster_name = self.config.cluster
        database = self.config.database

        self.client.execute(f"CREATE DATABASE IF NOT EXISTS {database} ON CLUSTER {cluster_name}")
        self.client.execute(
            f"CREATE TABLE IF NOT EXISTS {database}.{self.config.views_table_name} ON CLUSTER {cluster_name} \
                (user_id UUID, film_id UUID, number_seconds_viewing INTEGER, record_time DateTime) \
                    ENGINE = MergeTree() ORDER BY (user_id, film_id)"
        )
        self.client.execute("SET allow_experimental_object_type = 1;")
        self.client.execute(
            f"CREATE TABLE IF NOT EXISTS {database}.{self.config.custom_events_table_name} ON CLUSTER {cluster_name} \
                (user_id UUID, film_id UUID, event_type String, message JSON, record_time DateTime) \
                    ENGINE = MergeTree() ORDER BY (user_id, film_id)"
        )

    @backoff.on_exception(backoff.expo, Exception)
    def load(self, message: FilmViewEventDTO) -> int | None:
        """Метод для загрузки данных в Clickhouse."""
        data = [message]
        logging.error(data)
        query = f"""
            INSERT INTO shard.{self.config.views_table_name}
            (user_id, film_id, number_seconds_viewing, record_time) VALUES"""

        return self.client.execute(  # type: ignore[no-any-return]
            query, ((row.user_id, row.film_id, row.number_seconds_viewing, row.record_time) for row in data)
        )
