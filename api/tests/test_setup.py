import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.model import User


@pytest.mark.asyncio
async def test_setup_state_incomplete_on_fresh_db(client: AsyncClient):
    resp = await client.get("/api/v1/settings/setup/state")
    assert resp.status_code == 200
    data = resp.json()
    assert data["complete"] is False
    assert data["step"] == "welcome"


@pytest.mark.asyncio
async def test_setup_init_creates_owner_and_logs_in(client: AsyncClient):
    resp = await client.post(
        "/api/v1/settings/setup/init",
        json={
            "storage_path": "./data/recordings",
            "admin_username": "owner1",
            "admin_display_name": "Primary Owner",
            "admin_password": "supersecret1",
            "encryption_enabled": True,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["username"] == "owner1"
    assert data["user"]["display_name"] == "Primary Owner"
    assert data["user"]["role"] == "owner"

    # setup state now reports complete
    state = await client.get("/api/v1/settings/setup/state")
    assert state.json()["complete"] is True

    # the returned access token actually works
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["username"] == "owner1"


@pytest.mark.asyncio
async def test_setup_init_rejected_when_already_complete(client: AsyncClient):
    first = await client.post(
        "/api/v1/settings/setup/init",
        json={"admin_username": "owner1", "admin_password": "supersecret1"},
    )
    assert first.status_code == 201

    second = await client.post(
        "/api/v1/settings/setup/init",
        json={"admin_username": "owner2", "admin_password": "supersecret2"},
    )
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_setup_init_rejected_when_users_already_exist(
    client: AsyncClient, admin_user: User
):
    # setup_complete flag is still false, but a user already exists
    # (e.g. from the dev seed script) -- must not allow a second bootstrap.
    resp = await client.post(
        "/api/v1/settings/setup/init",
        json={"admin_username": "owner2", "admin_password": "supersecret2"},
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_setup_init_rejects_short_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/settings/setup/init",
        json={"admin_username": "owner1", "admin_password": "short"},
    )
    assert resp.status_code == 422
