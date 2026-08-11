import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_self_update_display_name(client: AsyncClient, auth_headers):
    resp = await client.put(
        "/api/v1/users/me",
        json={"display_name": "New Name"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["display_name"] == "New Name"


@pytest.mark.asyncio
async def test_self_update_password_requires_current_password(
    client: AsyncClient, auth_headers
):
    resp = await client.put(
        "/api/v1/users/me",
        json={"new_password": "brandnewpass123"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_self_update_password_wrong_current_password(
    client: AsyncClient, auth_headers
):
    resp = await client.put(
        "/api/v1/users/me",
        json={"current_password": "wrongpass", "new_password": "brandnewpass123"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_self_update_password_success_and_relogin(
    client: AsyncClient, auth_headers
):
    resp = await client.put(
        "/api/v1/users/me",
        json={"current_password": "testpass123", "new_password": "brandnewpass123"},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "testadmin", "password": "brandnewpass123"},
    )
    assert login_resp.status_code == 200


@pytest.mark.asyncio
async def test_delete_non_owner_user(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/users",
        json={
            "username": "deleteme",
            "display_name": "Delete Me",
            "password": "deletemepass123",
            "role": "viewer",
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/v1/users/{user_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    list_resp = await client.get("/api/v1/users", headers=auth_headers)
    usernames = [u["username"] for u in list_resp.json()]
    assert "deleteme" not in usernames


@pytest.mark.asyncio
async def test_cannot_delete_last_owner(client: AsyncClient, auth_headers, admin_user):
    resp = await client.delete(f"/api/v1/users/{admin_user.id}", headers=auth_headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_can_delete_owner_when_another_owner_exists(
    client: AsyncClient, auth_headers, admin_user
):
    create_resp = await client.post(
        "/api/v1/users",
        json={
            "username": "secondowner",
            "display_name": "Second Owner",
            "password": "secondownerpass123",
            "role": "owner",
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201

    resp = await client.delete(f"/api/v1/users/{admin_user.id}", headers=auth_headers)
    assert resp.status_code == 204
