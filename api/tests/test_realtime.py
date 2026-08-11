import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_realtime_status_requires_auth(client: AsyncClient):
    resp = await client.get("/api/v1/realtime/status")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_realtime_status_ok(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/realtime/status", headers=auth_headers)
    assert resp.status_code == 200
    assert "connected_clients" in resp.json()


@pytest.mark.asyncio
async def test_get_default_alert_settings(client: AsyncClient, auth_headers):
    resp = await client.get("/api/v1/realtime/settings", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["websocket_enabled"] is True
    assert body["lan_broadcast_enabled"] is True
    assert body["lan_broadcast_port"] == 37020
    assert body["min_importance"] == "low"


@pytest.mark.asyncio
async def test_update_alert_settings_requires_owner(client: AsyncClient):
    resp = await client.put(
        "/api/v1/realtime/settings",
        json={"min_importance": "high"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_update_and_persist_alert_settings(client: AsyncClient, auth_headers):
    resp = await client.put(
        "/api/v1/realtime/settings",
        json={"min_importance": "high", "lan_broadcast_enabled": False},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["min_importance"] == "high"
    assert body["lan_broadcast_enabled"] is False
    # unrelated field should be preserved from defaults
    assert body["websocket_enabled"] is True

    reread = await client.get("/api/v1/realtime/settings", headers=auth_headers)
    assert reread.json()["min_importance"] == "high"
    assert reread.json()["lan_broadcast_enabled"] is False
