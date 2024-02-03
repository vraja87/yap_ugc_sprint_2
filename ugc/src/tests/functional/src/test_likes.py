import uuid

import pytest


pytestmark = pytest.mark.asyncio(scope="module")


class TestLike:

    film_id = [str(uuid.uuid4()) for i in range(10)]
    review_id = []
    
    async def test_adding_fixture(self, async_client, access_token):
        for id in self.film_id:
            response = await async_client.post(
                "api/v1/interactions/add_review",
                headers={
                    "X-Request-Id": "123",
                    "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
                json={"film_id": id, "review_text": str(uuid.uuid4())}
            )

            assert response.status_code == 200
            assert bool(response.json()) is True
            self.review_id.append(response.json())

    @pytest.mark.dependency(depends=["test_adding_fixture"])
    async def test_add_like(self, async_client, access_token):
        for id in self.film_id:
            response = await async_client.post(
                "api/v1/interactions/rate_film",
                headers={
                    "X-Request-Id": "123",
                    "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
                params={"film_id": id, "is_like": True}
            )
            assert response.status_code == 200
            assert bool(response.json()) is True
        for id in self.review_id:
            response = await async_client.post(
                "api/v1/interactions/rate_review",
                headers={
                    "X-Request-Id": "123",
                    "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
                params={"review_id": id, "is_like": True}
            )
            assert response.status_code == 200
            assert bool(response.json()) is True

    @pytest.mark.dependency(depends=["test_add_like"])
    async def test_add_dislike(self, async_client, access_token):
        response = await async_client.post(
            "api/v1/interactions/rate_film",
            headers={
                "X-Request-Id": "123",
                "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
            params={"film_id": self.film_id[0], "is_like": False}
        )
        assert response.status_code == 200
        assert bool(response.json()) is False
        response = await async_client.post(
            "api/v1/interactions/rate_review",
            headers={
                "X-Request-Id": "123",
                "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
            params={"review_id": self.review_id[0], "is_like": False}
        )
        assert response.status_code == 200
        assert bool(response.json()) is False

    @pytest.mark.dependency(depends=["test_add_dislike"])
    async def test_get_likes(self, async_client, access_token):
        for id in self.film_id:
            response = await async_client.get(
                f"api/v1/interactions/film_likes?film_id={id}",
                headers={
                    "X-Request-Id": "123",
                    "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
            )
            assert response.status_code == 200
            assert response.json()["like_film"] == 1
        for id in self.review_id:
            response = await async_client.get(
                f"api/v1/interactions/review_likes?review_id={id}",
                headers={
                    "X-Request-Id": "123",
                    "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
            )
            assert response.status_code == 200
            assert response.json()["like_review"] == 1

    @pytest.mark.dependency(depends=["test_get_likes"])
    async def test_add_rating(self, async_client, access_token):
        for id in self.film_id:
            response = await async_client.post(
                "api/v1/interactions/estimate_film",
                headers={
                    "X-Request-Id": "123",
                    "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
                json={"film_id": id, "rating": 6.6}
            )
            assert response.status_code == 200

    @pytest.mark.dependency(depends=["test_add_rating"])
    async def test_likes_remove(self, async_client, access_token):
        for id in self.film_id:
            response = await async_client.post(
                "api/v1/interactions/remove_film_like",
                headers={
                    "X-Request-Id": "123",
                    "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
                params={"film_id": id}
            )
            assert response.status_code == 200
            assert response.json() == 1

    @pytest.mark.dependency(depends=["test_likes_remove"])
    async def test_rating(self, async_client, access_token):
        response = await async_client.get(
            f"api/v1/interactions/film_rating?film_id={self.film_id[0]}",
            headers={
                "X-Request-Id": "123",
                "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
        )
        assert response.status_code == 200
        assert response.json() == 6.6
