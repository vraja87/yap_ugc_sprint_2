import multiprocessing
import random
from abc import ABCMeta, abstractmethod
from datetime import datetime
from time import sleep
from uuid import UUID

import vertica_python
from clickhouse_driver import Client
from faker import Faker


class DcConnectVertica:
    """Manages the connection to a Vertica database."""

    def __init__(self, dsl_dict: dict = None) -> None:
        self.dsl_dict = dsl_dict
        self.connection, self.cursor = self.connect()

    def connect(self):
        """Establishes and returns a connection to the Vertica database along with a cursor for queries.
        It uses the connection-details specified in dsl_dict field."""
        connection = vertica_python.connect(**self.dsl_dict)
        cursor = connection.cursor()
        return connection, cursor

    def disconnect(self) -> None:
        """Clean and safe disconnection from the database."""
        self.cursor.close()
        self.connection.commit()
        self.connection.close()

    def __del__(self) -> None:
        """Class destructor that ensures the database connection is properly closed."""
        try:
            if self.connection is not None:
                self.disconnect()
        except Exception:
            pass


class TestDb(metaclass=ABCMeta):
    """ABC that defines a template for database testing."""

    def __init__(
        self, connection_info: dict, total_rows: int, batch_size: int, delay_for_parallel_processes: int
    ):
        self.connection_info = connection_info
        self.total_rows = total_rows
        self.batch_size = batch_size
        self.delay_for_parallel_processes = delay_for_parallel_processes

    @abstractmethod
    def drop_db_table(self) -> None:
        pass

    @abstractmethod
    def create_db_table(self) -> None:
        pass

    @abstractmethod
    def insert_data(self) -> None:
        pass

    @abstractmethod
    def read_data(self) -> None:
        pass

    @abstractmethod
    def process_loaded_data(self) -> None:
        pass

    def parallel_insert_and_read(self) -> None:
        """Starts two separate processes: data insertion, and data reading, with a specified delay between them."""
        print("process insert_data")
        p1 = multiprocessing.Process(target=self.insert_data)
        p1.start()

        sleep(self.delay_for_parallel_processes)
        print("process read_data")
        p2 = multiprocessing.Process(target=self.read_data)

        p2.start()

        p1.join()
        p2.join()

    def test_all(self) -> None:
        """Runs a complete suite of tests on a database."""
        self.drop_db_table()
        self.create_db_table()
        self.insert_data()
        self.read_data()
        self.process_loaded_data()
        self.parallel_insert_and_read()
        self.drop_db_table()


class TestVertica(TestDb):
    """Tests for vertica database"""

    def drop_db_table(self):
        connect = DcConnectVertica(self.connection_info)
        connect.cursor.execute("""DROP TABLE IF EXISTS views;""")

    def create_db_table(self):
        connect = DcConnectVertica(self.connection_info)
        connect.cursor.execute(
            """
        CREATE TABLE views (
            id IDENTITY,
            user_id INTEGER NOT NULL,
            movie_id VARCHAR(256) NOT NULL,
            viewed_frame INTEGER NOT NULL
        );
        """
        )

    def insert_data(self):
        print("start insert_data test")
        connect = DcConnectVertica(self.connection_info)
        start_time = datetime.now()
        batch = []
        for _ in range(self.total_rows):
            record = generate_record()
            batch.append(record)
            if len(batch) == self.batch_size:
                connect.cursor.executemany(
                    "INSERT INTO views (user_id, movie_id, viewed_frame) VALUES (%s, %s, %s)",
                    batch,
                )
                batch = []
        if batch:
            connect.cursor.executemany(
                "INSERT INTO views (user_id, movie_id, viewed_frame) VALUES (%s, %s, %s)",
                batch,
            )
        end_time = datetime.now()
        print(
            f"insert {self.total_rows} with batches {self.batch_size} rows in {end_time - start_time} seconds"
        )

    def read_data(self):
        print("start read_data test")
        connect = DcConnectVertica(self.connection_info)
        start_time = datetime.now()
        connect.cursor.execute(f"SELECT * FROM views limit {self.total_rows}")
        rows = connect.cursor.fetchall()
        # pprint(rows)
        end_time = datetime.now()
        rows_count = len(rows)
        print(f"Read {rows_count} rows in {end_time - start_time} seconds")
        assert rows_count >= self.total_rows

    def process_loaded_data(self):
        print("start data processing test")
        connect = DcConnectVertica(self.connection_info)
        start_time = datetime.now()
        connect.cursor.execute(
            "SELECT movie_id, COUNT(*) AS views_count, AVG(viewed_frame) AS average_viewed_frame "
            "FROM views GROUP BY movie_id"
        )
        end_time = datetime.now()
        print(f"Processed loaded data in {end_time - start_time} seconds")


class TestClickHouse(TestDb):
    """Tests for ClickHouse database"""

    def drop_db_table(self):
        client = Client(**self.connection_info)
        client.execute(
            """
            DROP TABLE IF EXISTS views;
            """
        )

    def create_db_table(self):
        client = Client(**self.connection_info)
        client.execute(
            """
            CREATE TABLE IF NOT EXISTS views
            (
                id UUID DEFAULT generateUUIDv4(),
                user_id Int64,
                movie_id UUID,
                viewed_frame Int64
            ) engine=MergeTree()
            ORDER BY (user_id, movie_id);
            """
        )

    def insert_data(self):
        print("start insert_data test")
        client = Client(**self.connection_info)
        start_time = datetime.now()
        batch = []
        for _ in range(total_rows):
            record = generate_record()
            batch.append(record)
            if len(batch) == self.batch_size:
                client.execute(
                    "INSERT INTO views (user_id, movie_id, viewed_frame) VALUES", batch
                )
                batch = []
        if batch:
            client.execute(
                "INSERT INTO views (user_id, movie_id, viewed_frame) VALUES", batch
            )
        end_time = datetime.now()
        print(
            f"insert {self.total_rows} with batches {self.batch_size} rows in {end_time - start_time} seconds"
        )

    def read_data(self):
        client = Client(**self.connection_info)
        print("start read_data test")
        start_time = datetime.now()
        rows = client.execute(f"SELECT * FROM views limit {self.total_rows}")
        # pprint(rows)
        end_time = datetime.now()
        rows_count = len(rows)
        print(f"Read {rows_count} rows in {end_time - start_time} seconds")
        assert rows_count >= total_rows

    def process_loaded_data(self):
        client = Client(**self.connection_info)
        print("start data processing test")
        start_time = datetime.now()
        client.execute(
            "SELECT movie_id, COUNT(*) AS views_count, AVG(viewed_frame) AS average_viewed_frame "
            "FROM views GROUP BY movie_id"
        )
        end_time = datetime.now()
        print(f"Processed loaded data in {end_time - start_time} seconds")


fake = Faker()


def generate_record() -> tuple[int, UUID, int]:
    """Universal utility function to generate a random record for database insertion"""
    user_id = random.randint(1, 1000)
    movie_id = fake.uuid4()
    viewed_frame = random.randint(1, 1000)
    return user_id, movie_id, viewed_frame


if __name__ == "__main__":
    """Initializes and runs a series of database tests for both Vertica and ClickHouse databases.
    It creates instances of TestVertica and TestClickHouse, running a full suite of tests
    on each database type for a specified number of iterations.
    """

    total_rows = 10_000_000
    batch_size = 1000
    delay_for_parallel_processes = 20
    turns = 10

    vertica_connection_info = {
        "host": "127.0.0.1",
        "port": 5435,
        "user": "dbadmin",
        "password": "",
        "database": "docker",
        "autocommit": True,
    }
    click_connection_info = {
        "host": "localhost",
    }

    for i in range(1, turns + 1):
        vertica = TestVertica(
            vertica_connection_info,
            total_rows,
            batch_size,
            delay_for_parallel_processes,
        )
        click = TestClickHouse(
            click_connection_info, total_rows, batch_size, delay_for_parallel_processes
        )
        print(f"turn {i}")
        print("vertica")
        vertica.test_all()
        del vertica
        print("click")
        click.test_all()
        del click
