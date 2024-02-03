import os
import uuid

import asyncio
import pytest
import pytest_asyncio
import requests

from fastapi import FastAPI
from httpx import AsyncClient

from typing import AsyncGenerator


from core.config import mongo_settings

from storage import mq, nosql
from main import app


@pytest_asyncio.fixture(scope="session")
async def fastapi_app() -> FastAPI:
    mq.queue_producer = mq.KafkaProducer(bootstrap_servers="kafka-node1:9092")
    nosql.nosql = nosql.MongoDBConnector(
        db_name=mongo_settings.db, collection_name=mongo_settings.collection, hosts="mongodb://mongodb-test:27017"
    )
    collection = nosql.nosql.db[mongo_settings.collection]
    collection.delete_many({})

    yield app

    nosql.nosql.client.close()
    await mq.queue_producer.stop()


@pytest_asyncio.fixture(scope="session")
async def async_client(fastapi_app: FastAPI) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url="http://127.0.0.1:8000") as ac:
        yield ac


@pytest_asyncio.fixture(scope="session")
async def access_token():
    auth = requests.post(
        f"{os.getenv('AUTH_API_URL')}auth/login",
        headers={"X-Request-Id": "123"},
        json={"email": os.getenv("AUTH_TEST_USER_EMAIL"), "password": os.getenv("AUTH_TEST_USER_PASSWORD")},
    )
    access_token = auth.json()["access_token"]
    refresh_token = auth.json()["refresh_token"]

    yield access_token

    logout = requests.post(
        f"{os.getenv('AUTH_API_URL')}auth/logout",
        headers={
            "X-Request-Id": "123",
            "Cookie": f"access_token={access_token}; HttpOnly; Path=/, refresh_token={refresh_token}; HttpOnly; Path=/,",
        },
    )
    if not logout.status_code != 200:
        raise Exception("Tokens was not banned!")
