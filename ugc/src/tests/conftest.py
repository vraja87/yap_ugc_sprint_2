import asyncio

import pytest_asyncio

pytest_plugins = ["tests.fixtures.db"]


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
