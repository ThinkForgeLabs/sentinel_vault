import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_users_requires_owner(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/users", headers=auth_headers)
    assert resp.status_code == 200
    usernames = [u["username"] for u in resp.json()]
    assert "testadmin" in usernames


@pytest.mark.asyncio
async def test_create_and_update_user(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/users",
        json={
            "username": "viewer1",
            "display_name": "Viewer One",
            "password": "viewerpass123",
            "role": "viewer",
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/api/v1/users/{user_id}",
        json={"display_name": "Viewer One Updated"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["display_name"] == "Viewer One Updated"
