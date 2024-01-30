import asyncio
import os
import random
import sys
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from uuid import uuid4, UUID

import asyncpg
import bson
from faker import Faker

current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.join(current_path, '../../ugc/src')  # from service root
sys.path.append(parent_path)
from storage.mongo import get_user_interactions  # noqa: E402

fake = Faker()

# NUM_FILMS = 1000
# NUM_USERS = 10000
# NUM_REVIEWERS = 100
NUM_FILMS = 20
NUM_USERS = 100
NUM_REVIEWERS = 10
# 3 min insert by 1k rows


class AsyncPostgresConnector:
    def __init__(self, dbname, user, password, host, port):
        self.connection_info = {
            "database": dbname,
            "user": user,
            "password": password,
            "host": host,
            "port": port
        }

    @asynccontextmanager
    async def get_connection(self):
        connection = await asyncpg.connect(**self.connection_info)
        try:
            yield connection
        finally:
            await connection.close()

    async def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS user_interactions (
        id SERIAL PRIMARY KEY,
        user_id UUID NOT NULL,
        film_id UUID NOT NULL,
        timestamp TIMESTAMP NOT NULL,
        event_type VARCHAR(50) NOT NULL,
        rating SMALLINT,
        review_id UUID,
        review_text TEXT
        );
        """
        async with self.get_connection() as conn:
            await conn.execute(create_table_query)

    async def insert_data(self, data):
        insert_query = """
        INSERT INTO user_interactions (user_id, film_id, timestamp, event_type, rating, review_id, review_text)
        VALUES ($1, $2, $3, $4, $5, $6, $7);
        """
        async with self.get_connection() as conn:
            await conn.executemany(insert_query, data)

    async def get_bookmarked_films_by_user(self, user_id):
        select_query = """
        SELECT film_id FROM user_interactions
        WHERE user_id = $1 AND event_type = 'bookmark';
        """
        async with self.get_connection() as conn:
            rows = await conn.fetch(select_query, user_id)
            return [row['film_id'] for row in rows]

    async def check_new_like_appearance(self, film_id):
        select_query = """
        SELECT count(*) FROM user_interactions
        WHERE film_id = $1 AND event_type = 'like_film';
        """
        async with self.get_connection() as conn:
            row = await conn.fetchrow(select_query, film_id)
            return row['count']

    async def get_likes_dislikes_count(self, film_id):
        select_query = """
        SELECT event_type, count(*) as count
        FROM user_interactions
        WHERE film_id = $1 AND event_type IN ('like_film', 'dislike_film')
        GROUP BY event_type;
        """
        async with self.get_connection() as conn:
            rows = await conn.fetch(select_query, film_id)
            return {row['event_type']: row['count'] for row in rows}

    async def get_liked_films_by_user(self, user_id):
        select_query = """
        SELECT film_id FROM user_interactions
        WHERE user_id = $1 AND event_type = 'like_film';
        """
        async with self.get_connection() as conn:
            rows = await conn.fetch(select_query, user_id)
            return [row['film_id'] for row in rows]

    async def get_average_film_rating(self, film_id):
        select_query = """
        SELECT AVG(rating) as average_rating
        FROM user_interactions
        WHERE film_id = $1 AND event_type = 'rating';
        """
        async with self.get_connection() as conn:
            row = await conn.fetchrow(select_query, film_id)
            return row['average_rating'] if row['average_rating'] is not None else 0

    async def insert_film_like_dislike(self, user_id, film_id, is_like=True):
        rating = 10 if is_like else 0
        event_type = 'like_film' if is_like else 'dislike_film'
        data = (user_id, film_id, datetime.now(), event_type, rating, None, None)
        await self.insert_data([data])

    async def insert_bookmark(self, user_id, film_id):
        data = (user_id, film_id, datetime.now(), 'bookmark', None, None, None)
        await self.insert_data([data])

    async def insert_review(self, user_id, film_id, review_text):
        data = (user_id, film_id, datetime.now(), 'review', None, None, review_text)
        await self.insert_data([data])

    async def insert_bulk_data(self, data):
        insert_query = """
        INSERT INTO user_interactions (user_id, film_id, timestamp, event_type, rating, review_id, review_text)
        VALUES ($1, $2, $3, $4, $5, $6, $7);
        """
        async with self.get_connection() as conn:
            await conn.executemany(insert_query, data)


def start_data_stack_generation():
    """Generating lists of UUIDs for movies, users and reviews (with text)"""
    film_ids = [uuid4() for _ in range(NUM_FILMS)]
    user_ids = [uuid4() for _ in range(NUM_USERS)]
    reviewer_ids = random.sample(user_ids, NUM_REVIEWERS)

    reviews = []

    for film_id in film_ids:
        if film_id in random.sample(film_ids, NUM_FILMS // 2):
            reviewer_id = random.choice(reviewer_ids)
            review_text = fake.text(max_nb_chars=200)
            reviews.append({'film_id': film_id, 'reviewer_id': reviewer_id, 'review_text': review_text})

        # Генерация доп. рецензий
        num_extra_reviews = random.randint(0, NUM_FILMS)
        for _ in range(num_extra_reviews):
            reviewer_id = random.choice(reviewer_ids)
            review_text = fake.text(max_nb_chars=200)
            reviews.append({'film_id': film_id, 'reviewer_id': reviewer_id, 'review_text': review_text})

    return film_ids, user_ids, reviews, reviewer_ids


async def insert_data_bulk(user_interactions, data):
    """Inserting data in batches."""
    if data:
        await user_interactions.collection.insert_many(data)


async def insert_initial_data_mongo(user_interactions, film_ids, user_ids, reviews):
    """Inserting likes, bookmarks and reviews in packages, in mongo format"""
    batch = []
    batch_size = 5000

    for film_id in film_ids:
        for user_id in user_ids:
            if random.random() < 0.5:  # лайки половине
                batch.append({
                    "user_id": bson.Binary.from_uuid(user_id),
                    "film_id": bson.Binary.from_uuid(film_id),
                    "timestamp": datetime.now(),
                    "event_type": "like_film",
                    "rating": 10
                })
            if random.random() < 0.1:  # в закладки ~10%
                batch.append({
                    "user_id": bson.Binary.from_uuid(user_id),
                    "film_id": bson.Binary.from_uuid(film_id),
                    "timestamp": datetime.now(),
                    "event_type": "bookmark"
                })

            if len(batch) >= batch_size:
                await insert_data_bulk(user_interactions, batch)
                batch = []

    for review in reviews:
        batch.append({
            "user_id": bson.Binary.from_uuid(review['reviewer_id']),
            "film_id": bson.Binary.from_uuid(review['film_id']),
            "timestamp": datetime.now(),
            "event_type": "review",
            "review_text": review['review_text']
        })

        if len(batch) >= batch_size:
            await insert_data_bulk(user_interactions, batch)
            batch = []

    await insert_data_bulk(user_interactions, batch)


async def insert_initial_data_psql(user_interactions, film_ids, user_ids, reviews):
    """Inserting data in psql format, likes for a half of films and bookmarks ~10%"""
    batch_size = 1000
    batch = []
    for film_id in film_ids:
        for user_id in user_ids:
            timestamp = datetime.now()
            if random.random() < 0.5:
                batch.append((user_id, film_id, timestamp, 'like_film', 10, None, None))
            if random.random() < 0.1:
                batch.append((user_id, film_id, timestamp, 'bookmark', None, None, None))

            if len(batch) >= batch_size:
                await user_interactions.insert_bulk_data(batch)
                batch = []

    for review in reviews:
        timestamp = datetime.now()
        reviewer_id = review['reviewer_id']
        film_id = review['film_id']
        review_text = review['review_text']
        batch.append((reviewer_id, film_id, timestamp, 'review', None, uuid4(), review_text))

        if len(batch) >= batch_size:
            await user_interactions.insert_bulk_data(batch)
            batch = []

    # Для оставшихся записей
    if batch:
        await user_interactions.insert_bulk_data(batch)


async def main(db_name):
    if db_name == 'psql':
        user_interactions = AsyncPostgresConnector('mydatabase', 'myuser', 'mypassword', 'localhost', 5432)
        await user_interactions.create_table()
        init_data = insert_initial_data_psql
    else:
        init_data = insert_initial_data_mongo
        user_interactions = await get_user_interactions()

    film_ids, user_ids, reviews, _ = start_data_stack_generation()

    start_time = datetime.now()
    await init_data(user_interactions, film_ids, user_ids, reviews)
    end_time = datetime.now()
    print('Total Insertion Time:', end_time - start_time)

    time_get_bookmarked_films_by_user = []
    time_get_likes_dislikes_count = []
    time_get_liked_films_by_user = []
    time_get_average_film_rating = []

    for i in range(0, 100):
        user_id = user_ids[i]
        end_time, start_time = await perform_test(user_interactions.get_bookmarked_films_by_user, user_id)
        time_get_bookmarked_films_by_user.append(end_time - start_time)
        end_time, start_time = await perform_test(user_interactions.get_liked_films_by_user, user_id)
        time_get_liked_films_by_user.append(end_time - start_time)
    await print_time(time_get_bookmarked_films_by_user, user_interactions.get_bookmarked_films_by_user.__name__)
    await print_time(time_get_liked_films_by_user, user_interactions.get_liked_films_by_user.__name__)

    for _ in range(0, 100):
        i = random.randrange(2, NUM_FILMS)
        film_id = film_ids[i]
        end_time, start_time = await perform_test(user_interactions.get_likes_dislikes_count, film_id)
        time_get_likes_dislikes_count.append(end_time - start_time)
        end_time, start_time = await perform_test(user_interactions.get_average_film_rating, film_id)
        time_get_average_film_rating.append(end_time - start_time)
    await print_time(time_get_average_film_rating, user_interactions.get_average_film_rating.__name__)
    await print_time(time_get_likes_dislikes_count, user_interactions.get_likes_dislikes_count.__name__)

    await asyncio.gather(
        init_data(user_interactions, film_ids, user_ids, reviews),
        check_fresh_like(film_ids, user_ids, user_interactions)
    )


async def perform_test(func_, some_id):
    """Performs one test, returns the time of its execution"""
    start_time = datetime.now()
    await func_(some_id)
    end_time = datetime.now()
    return end_time, start_time


async def check_fresh_like(film_ids: list[UUID], user_ids: list[UUID], user_interactions):
    time_get_liked_films_by_user = []
    time_get_likes_dislikes_count = []

    film_ids_set = set(film_ids)

    for _ in range(0, 100):
        random_user = user_ids[random.randrange(2, 20)]
        liked_films = await user_interactions.get_liked_films_by_user(random_user)

        unliked_film_result = next(iter(film_ids_set - set(liked_films)), None)
        if unliked_film_result is None:
            continue

        unliked_film = unliked_film_result

        old_likes_count = await user_interactions.get_likes_dislikes_count(unliked_film)
        await user_interactions.insert_film_like_dislike(random_user, unliked_film)
        start_time = datetime.now()
        for like_try_count in range(0, 100):
            new_likes_count = await user_interactions.get_likes_dislikes_count(unliked_film)
            if new_likes_count['like_film'] > old_likes_count['like_film']:
                break
        end_time = datetime.now()
        time_get_likes_dislikes_count.append(end_time - start_time)

        random_user = user_ids[random.randrange(2, 20)]
        liked_films = await user_interactions.get_liked_films_by_user(random_user)
        unliked_film_result = next(iter(film_ids_set - set(liked_films)), None)

        unliked_film = unliked_film_result
        if unliked_film_result is None:
            continue

        await user_interactions.insert_film_like_dislike(random_user, unliked_film)
        start_time = datetime.now()
        for like_try in range(0, 100):
            new_liked_films = await user_interactions.get_liked_films_by_user(random_user)
            if unliked_film in new_liked_films:
                break
        end_time = datetime.now()
        time_get_liked_films_by_user.append(end_time - start_time)

    await print_time(time_get_likes_dislikes_count, user_interactions.get_likes_dislikes_count.__name__)
    await print_time(time_get_liked_films_by_user, user_interactions.get_liked_films_by_user.__name__)


async def print_time(collection, collection_name):
    min_time = min(collection).total_seconds() * 1000
    max_time = max(collection).total_seconds() * 1000
    avg_time = sum(collection, timedelta()).total_seconds() * 1000 / len(collection)
    print(collection_name)
    print(f' - min `{min_time:.2f}` ms max `{max_time:.2f}` ms avg `{avg_time:.2f}` ms')


if __name__ == "__main__":
    asyncio.run(main('mongo'))
    asyncio.run(main('psql'))
