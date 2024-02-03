import uuid

import pytest


pytestmark = pytest.mark.asyncio(scope="module")


class TestLike:

    film_id = [str(uuid.uuid4()) for i in range(10)]

    async def test_add_review(self, async_client, access_token):
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

    @pytest.mark.dependency(depends=["test_add_review"])
    async def test_update_review(self, async_client, access_token):
        for id in self.film_id:
            response = await async_client.post(
                "api/v1/interactions/update_review",
                headers={
                    "X-Request-Id": "123",
                    "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
                json={"film_id": id, "review_text": str(uuid.uuid4())}
            )
            assert response.status_code == 200
            assert bool(response.json()) is True

    @pytest.mark.dependency(depends=["test_update_review"])
    async def test_remove_review(self, async_client, access_token):
        for id in self.film_id:
            response = await async_client.post(
                "api/v1/interactions/remove_review",
                headers={
                    "X-Request-Id": "123",
                    "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
                params={"film_id": id}
            )
            assert response.status_code == 200
            assert response.json() == 1