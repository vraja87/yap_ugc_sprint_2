from abc import ABC, abstractmethod

import motor.motor_asyncio
from bson.objectid import ObjectId

from ugc.src.core.config import mongo_settings


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
    async def delete_one(self, id_: str):
        pass

    @abstractmethod
    async def count(self, query: dict):
        pass


class MongoDBConnector(NoSqlDb):
    def __init__(self, db_name: str, collection_name: str, hosts: str):
        connection_uri = f"mongodb://{hosts}"
        self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    async def insert_record(self, record: dict):
        result = await self.collection.insert_one(record)
        return str(result.inserted_id)

    async def find_records(self, query: dict):
        cursor = self.collection.find(query)
        return await cursor.to_list(length=None)

    async def find_one(self, id_: str):
        doc = await self.collection.find_one({"_id": ObjectId(id_)})
        return doc

    async def update_one(self, filter_: dict, data_: dict):
        """
        filter_: {'user_id': ..., 'movie_id': ...}

        `user_id` needed to be in filter because it's a 'hashed field'. or you will get an error.
        """
        if 'user_id' not in filter_:
            raise ValueError("The filter_ must include 'user_id' for sharding without errors")

        update = {'$set': data_}
        return await self.collection.update_one(filter_, update, upsert=True)

    async def delete_one(self, id_: str):
        filter_ = {'_id': ObjectId(id_)}
        result = await self.collection.delete_one(filter_)
        return result.deleted_count

    async def count(self, query):
        """query: {"film_id": "..."}"""
        return await self.collection.count_documents(query)


class UserInteractions(MongoDBConnector):
    async def get_average_movie_rating(self, film_id: str):
        """
        Calculates the average score for a movie based on its film_id.
        """
        pipeline = [
            {"$match": {"film_id": film_id}},
            {"$group": {"_id": "$film_id", "average_rating": {"$avg": "$range"}}}
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=1)
        if result:
            return result[0]["average_rating"]
        else:
            return None

    async def get_bookmarked_movies_by_user(self, user_id: str):
        pipeline = [
            {"$match": {"user_id": user_id, "event_type": "bookmark"}},
            {"$group": {"_id": "$movie_id"}}
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=None)
        return [doc['_id'] for doc in result]

    async def get_likes_dislikes_count(self, movie_id: str):
        pipeline = [
            {"$match": {"movie_id": movie_id, "event_type": {"$in": ["like", "dislike"]}}},
            {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=None)
        return {doc['_id']: doc['count'] for doc in result}

    async def get_liked_movies_by_user(self, user_id: str):
        pipeline = [
            {"$match": {"user_id": user_id, "event_type": "like"}},
            {"$group": {"_id": "$movie_id"}}
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=None)
        return [doc['_id'] for doc in result]


mongo_connector = MongoDBConnector(
    db_name=mongo_settings.db,
    collection_name=mongo_settings.collection,
    hosts=mongo_settings.hosts
)


async def get_mongo_connector() -> MongoDBConnector:
    return mongo_connector
