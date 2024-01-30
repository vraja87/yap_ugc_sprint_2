from datetime import datetime
from uuid import UUID
from functools import lru_cache

from fastapi import Depends

import bson
from bson.objectid import ObjectId

from storage.nosql import MongoDBConnector, get_nosql
from models.interactions import Rating


class LikeService:
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
    def __init__(self, nosql: MongoDBConnector):
        self.nosql = nosql

    async def get_review_likes_dislikes_count(self, review_id: str):
        """Количество лайков и дизлайков у определённой рецензии"""
        result = await self.nosql.aggregate(
            [
                {"$match": {
                    "review_id": ObjectId(review_id),
                    "event_type": {"$in": ["like_review", "dislike_review"]}
                }},
                {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
            ]
        )
        return {doc['_id']: doc['count'] for doc in result}

    async def get_film_likes_dislikes_count(self, film_id: UUID):
        """Количество лайков и дизлайков у определённого фильма"""
        result = await self.nosql.aggregate(
            [
                {"$match": {
                    "film_id": bson.Binary.from_uuid(film_id),
                    "event_type": {"$in": ["like_film", "dislike_film"]}
                }},
                {"$group": {"_id": "$event_type", "count": {"$sum": 1}}}
            ]
        )
        return {doc['_id']: doc['count'] for doc in result}

    async def insert_film_like_dislike(self, user_id: UUID, film_id: UUID, is_like: bool = True):
        """
        Inserts an entry about the user's like/dislike of the film.
        """
        event = await self.nosql.find_one({
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
            "event_type": {"$in": ["like_film", "dislike_film"]}
        })
        if event:
            return None
        else:
            record = {
                "user_id": bson.Binary.from_uuid(user_id),
                "film_id": bson.Binary.from_uuid(film_id),
                "timestamp": datetime.now(),
                "event_type": "like_film" if is_like else "dislike_film",
            }
            return await self.nosql.insert_record(record)

    async def insert_review_like_dislike(self, user_id: UUID, review_id: ObjectId, is_like: bool = True):
        """
        Inserts an entry about the user's like/dislike of the review.
        """
        event = await self.nosql.find_one({
            "user_id": bson.Binary.from_uuid(user_id),
            "review_id": ObjectId(review_id),
            "event_type": {"$in": ["like_review", "dislike_review"]}
        })
        if event:
            return None
        else:
            record = {
                "user_id": bson.Binary.from_uuid(user_id),
                "review_id": ObjectId(review_id),
                "timestamp": datetime.now(),
                "event_type": "like_review" if is_like else "dislike_review"
            }
            return await self.nosql.insert_record(record)

    async def insert_rating(self, user_id: UUID, film_id: UUID, rating: float):
        """
        Inserts an entry about the user's like/dislike of the review.
        """
        await self.nosql.delete({
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
            "event_type": "rating"
        })
        record = {
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
            "timestamp": datetime.now(),
            "event_type": "rating",
            "rating": rating
        }
        return await self.nosql.insert_record(record)

    async def remove_film_like(self, user_id: UUID, film_id: UUID):
        """
        Inserts an entry about the user bookmarking the film.
        """
        record = {
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
            "event_type": {"$in": ["like_film", "dislike_film"]}
        }
        return await self.nosql.delete(record)

    async def remove_review_like(self, user_id: UUID, review_id: UUID):
        """
        Inserts an entry about the user bookmarking the film.
        """
        record = {
            "user_id": bson.Binary.from_uuid(user_id),
            "review_id": ObjectId(review_id),
            "event_type": {"$in": ["like_review", "dislike_review"]}
        }
        return await self.nosql.delete(record)

    async def get_average_film_rating(self, film_id: UUID):
        """Средняя пользовательская оценка фильма"""
        result = await self.nosql.aggregate(
            [
                {"$match": {"film_id": bson.Binary.from_uuid(film_id)}},
                {"$group": {"_id": "$film_id", "average_rating": {"$avg": "$rating"}}}
            ]
        )
        if result:
            return result[0]["average_rating"]
        else:
            return None


@lru_cache()
def get_like_service(
    nosql: MongoDBConnector = Depends(get_nosql),
) -> LikeService:
    return LikeService(nosql=nosql)
