from datetime import datetime
from uuid import UUID
from functools import lru_cache

from fastapi import Depends

import bson

from storage.nosql import MongoDBConnector, get_nosql


class BookmarkService:
    """
    user_id: Идентификатор пользователя.
    film_id: Идентификатор фильма.
    timestamp: Временная метка взаимодействия.
    event_type: bookmark
    """

    def __init__(self, nosql: MongoDBConnector):
        self.nosql = nosql

    async def get_bookmarked_films_by_user(self, user_id: UUID):
        """Список закладок"""
        result = await self.nosql.aggregate(
            [
                {"$match": {"user_id": bson.Binary.from_uuid(user_id), "event_type": "bookmark"}},
                {"$group": {"_id": "$film_id"}},
            ]
        )
        return {"result": [str(UUID(bytes=doc["_id"])) for doc in result]}

    async def insert_film_bookmark(self, user_id: UUID, film_id: UUID):
        """
        Inserts an entry about the user bookmarking the film.
        """
        event = await self.nosql.find_one(
            {
                "user_id": bson.Binary.from_uuid(user_id),
                "film_id": bson.Binary.from_uuid(film_id),
                "event_type": "bookmark",
            }
        )
        if event:
            return None
        else:
            record = {
                "user_id": bson.Binary.from_uuid(user_id),
                "film_id": bson.Binary.from_uuid(film_id),
                "timestamp": datetime.now(),
                "event_type": "bookmark",
            }
            return await self.nosql.insert_record(record)

    async def remove_bookmark(self, user_id: UUID, film_id: UUID):
        """
        Inserts an entry about the user bookmarking the film.
        """
        record = {
            "user_id": bson.Binary.from_uuid(user_id),
            "film_id": bson.Binary.from_uuid(film_id),
            "event_type": "bookmark",
        }
        return await self.nosql.delete(record)


@lru_cache()
def get_bookmark_service(
    nosql: MongoDBConnector = Depends(get_nosql),
) -> BookmarkService:
    return BookmarkService(nosql=nosql)
