import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_camera(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/cameras",
        json={
            "name": "Test Camera",
            "location_label": "Test Location",
            "rtsp_url": "rtsp://192.168.1.100:554/stream",
            "record_enabled": True,
            "ai_enabled": False,
            "retention_days": 14,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Test Camera"
    assert data["status"] == "offline"


@pytest.mark.asyncio
async def test_list_cameras(client: AsyncClient, auth_headers):
    # Create a camera first
    await client.post(
        "/api/v1/cameras",
        json={"name": "Cam1", "rtsp_url": "rtsp://1.2.3.4/stream"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/cameras", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_test_connection(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/cameras/test-connection",
        json={"rtsp_url": "rtsp://192.168.1.100:554/stream"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True


@pytest.mark.asyncio
async def test_test_connection_invalid(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/cameras/test-connection",
        json={"rtsp_url": "http://not-rtsp"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False