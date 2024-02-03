import uuid

import pytest

pytestmark = pytest.mark.asyncio(scope="module")


class TestAPI:
    async def test_read_main(self, async_client, access_token):
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestBookmark:

    film_id = [str(uuid.uuid4()) for i in range(10)]

    async def test_add_bookmark(self, async_client, access_token):
        for id in self.film_id:
            response = await async_client.post(
                "api/v1/interactions/set_bookmark",
                headers={"X-Request-Id": "123", "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
                params={"film_id": id},
            )
            assert response.status_code == 200
            assert bool(response.json()) is True

    @pytest.mark.dependency(depends=["test_add_bookmark"])
    async def test_add_bookmark_again(self, async_client, access_token):
        response = await async_client.get(
            "api/v1/interactions/my_bookmarks",
            headers={"X-Request-Id": "123", "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
        )
        assert response.status_code == 200
        assert len(response.json()["result"]) == len(self.film_id)

    @pytest.mark.dependency(depends=["test_add_bookmark_again"])
    async def test_remove_bookmark(self, async_client, access_token):
        for id in self.film_id:
            response = await async_client.post(
                "api/v1/interactions/remove_bookmark",
                headers={"X-Request-Id": "123", "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
                params={"film_id": id},
            )
            assert response.status_code == 200
            assert response.json() == 1

    @pytest.mark.dependency(depends=["test_remove_bookmark"])
    async def test_add_bookmark_deleted(self, async_client, access_token):
        response = await async_client.get(
            "api/v1/interactions/my_bookmarks",
            headers={"X-Request-Id": "123", "Cookie": f"access_token={access_token}; HttpOnly; Path=/"},
        )
        assert response.status_code == 200
        assert len(response.json()["result"]) == 0
