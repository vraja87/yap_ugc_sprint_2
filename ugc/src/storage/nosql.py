from abc import ABC, abstractmethod
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient


class NoSqlDb(ABC):
    @abstractmethod
    async def insert_record(self, record: dict):
        pass

    @abstractmethod
    async def find_records(self, query: dict):
        pass

    @abstractmethod
    async def update_one(self, filter_: dict, data: dict):
        pass

    @abstractmethod
    async def delete(self, filter: dict):
        pass

    @abstractmethod
    async def count(self, query: dict):
        pass

    @abstractmethod
    async def aggregate(self, pipeline: list[dict[str, Any]]):
        pass


class MongoDBConnector(NoSqlDb):
    def __init__(self, db_name: str, collection_name: str, hosts: str):
        connection_uri = f"mongodb://{hosts}"
        self.client = AsyncIOMotorClient(connection_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    async def insert_record(self, record: dict) -> str:
        """returns str(ObjectId)"""
        result = await self.collection.insert_one(record)
        return str(result.inserted_id)

    async def find_records(self, query: dict):
        cursor = self.collection.find(query)
        return await cursor.to_list(length=None)

    async def find_one(self, query: dict):
        doc = await self.collection.find_one(query)
        return doc

    async def update_one(self, filter_: dict, data_: dict):
        """
        filter_: {'user_id': ..., 'film_id': ...}

        `user_id` needed to be in filter because it's a 'hashed field'. or you will get an error.
        """
        if "user_id" not in filter_:
            raise ValueError("The filter_ must include 'user_id' for sharding without errors")

        update = {"$set": data_}
        result = await self.collection.update_one(filter_, update, upsert=True)
        return str(result.modified_count)

    async def delete(self, filter: dict):
        result = await self.collection.delete_many(filter)
        return result.deleted_count

    async def count(self, query):
        """query: {"film_id": "..."}"""
        return await self.collection.count_documents(query)

    async def aggregate(self, pipeline):
        """pipeline:
        [
            {"$match": {"film_id": "...."},
            {"$group": {"_id": ".....", "...."}}
        ]
        """
        return await self.collection.aggregate(pipeline).to_list(length=None)


nosql = MongoDBConnector


async def get_nosql() -> MongoDBConnector:
    return nosql
