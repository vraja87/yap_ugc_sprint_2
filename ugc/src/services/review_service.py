from datetime import datetime
from uuid import UUID
from functools import lru_cache

from fastapi import Depends

import bson
from storage.nosql import MongoDBConnector, get_nosql


class ReviewService:
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

    async def insert_review_text(self, user_id: UUID, film_id: UUID, review_text: str):
        event = await self.nosql.find_one({
            "event_type": "review",
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
        })
        if event:
            return None
        else:
            record = {
                "event_type": "review",
                "user_id": bson.Binary.from_uuid(user_id),
                "film_id": bson.Binary.from_uuid(film_id),
                "review_text": review_text,
                "timestamp": datetime.now()
            }
            return await self.nosql.insert_record(record)

    async def update_review_text(self, user_id: UUID, film_id: UUID, review_text: str):
        record = {
            "event_type": "review",
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
            "review_text": review_text,
            "timestamp": datetime.now()
        }
        filter = {
            "event_type": "review",
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
        }
        return await self.nosql.update_one(filter, record)

    async def remove_review(self, user_id: UUID, film_id: UUID):

        record = {
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
            "event_type": "review"
        }
        return await self.nosql.delete(record)


@lru_cache()
def get_review_service(
    nosql: MongoDBConnector = Depends(get_nosql),
) -> ReviewService:
    return ReviewService(nosql=nosql)
