from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

import bson
import motor.motor_asyncio
from bson.objectid import ObjectId

from core.config import mongo_settings


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

    async def insert_record(self, record: dict) -> str:
        """returns str(ObjectId)"""
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
        filter_: {'user_id': ..., 'film_id': ...}

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
    """
    типы событий: like_film, like_review, bookmark, rating, review

    user_id: Идентификатор пользователя.
    film_id: Идентификатор фильма.
    timestamp: Временная метка взаимодействия.
    event_type: Тип взаимодействия (например, лайк фильму, рецензия, закладка и т.д.).

    rating: Оценка фильма (10 для лайка, 0 для дизлайка).

    review_id: Уникальный идентификатор рецензии, - здесь это не UUID а ObjectId строки рецензии в базе.
    text: Текст рецензии.
    """

    async def get_average_film_rating(self, film_id: UUID):
        """Средняя пользовательская оценка фильма"""
        pipeline = [
            {"$match": {"film_id": bson.Binary.from_uuid(film_id)}},
            {"$group": {"_id": "$film_id", "average_rating": {"$avg": "$rating"}}}
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=1)
        if result:
            return result[0]["average_rating"]
        else:
            return None

    async def get_bookmarked_films_by_user(self, user_id: UUID):
        """Список закладок"""
        pipeline = [
            {"$match": {"user_id": bson.Binary.from_uuid(user_id), "event_type": "bookmark"}},
            {"$group": {"_id": "$film_id"}}
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=None)
        return [UUID(bytes=doc['_id']) for doc in result]

    async def get_likes_dislikes_count(self, film_id: UUID):
        """Количество лайков или дизлайков у определённого фильма"""
        pipeline = [
            {"$match": {"film_id": bson.Binary.from_uuid(film_id), "event_type": {"$in": ["like", "dislike"]}}},
            {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=None)
        return {doc['_id']: doc['count'] for doc in result}

    async def get_liked_films_by_user(self, user_id: UUID):
        """Список понравившихся пользователю фильмов (список лайков пользователя)"""
        pipeline = [
            {"$match": {"user_id": bson.Binary.from_uuid(user_id), "event_type": "like"}},
            {"$group": {"_id": "$film_id"}}
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=None)
        return [doc['_id'] for doc in result]

    async def insert_film_like_dislike(self, user_id: UUID, film_id: UUID, is_like: bool = True):
        """
        Inserts an entry about the user's like/dislike of the film.
        """
        record = {
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
            "timestamp": datetime.now(),
            "event_type": "like_film",
            "rating": 10 if is_like else 0,
        }
        return await self.insert_record(record)

    async def insert_review_text(self, user_id: UUID, film_id: UUID, review_text: str):
        record = {
            "event_type": "review",
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
            "review_text": review_text,
            "timestamp": datetime.now()
        }
        return await self.insert_record(record)

    async def insert_film_bookmark(self, user_id: UUID, film_id: UUID):
        """
        Inserts an entry about the user bookmarking the film.
        """
        record = {
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
            "timestamp": datetime.now(),
            "event_type": "bookmark"
        }
        return await self.insert_record(record)

    async def insert_review_like_dislike(self, user_id: UUID, review_id: ObjectId, is_like: bool = True):
        """
        Inserts an entry about the user's like/dislike of the review.
        """
        record = {
            "user_id": bson.Binary.from_uuid(user_id),
            "review_id": review_id,
            "timestamp": datetime.now(),
            "event_type": "like_review",
            "rating": 10 if is_like else 0
        }
        return await self.insert_record(record)

    async def insert_rating(self, user_id: UUID, film_id: UUID, rating: int):
        """
        Inserts an entry about the user's rating of the film.
        """
        record = {
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
            "timestamp": datetime.now(),
            "event_type": "rating",
            "rating": rating
        }
        return await self.insert_record(record)


mongo_connector = MongoDBConnector(
    db_name=mongo_settings.db,
    collection_name=mongo_settings.collection,
    hosts=mongo_settings.hosts
)


async def get_mongo_connector() -> MongoDBConnector:
    return mongo_connector
