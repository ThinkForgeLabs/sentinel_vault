from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


async def _create_camera(client: AsyncClient, auth_headers, name: str) -> str:
    resp = await client.post(
        "/api/v1/cameras",
        json={"name": name, "rtsp_url": "rtsp://10.0.0.9/stream"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_batch_availability_empty(client: AsyncClient, auth_headers):
    cam1 = await _create_camera(client, auth_headers, "WallCam1")
    cam2 = await _create_camera(client, auth_headers, "WallCam2")

    now = datetime.now(timezone.utc)
    resp = await client.post(
        "/api/v1/playback/availability/batch",
        json={
            "camera_ids": [cam1, cam2],
            "start": (now - timedelta(hours=1)).isoformat(),
            "end": now.isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert set(body["cameras"].keys()) == {cam1, cam2}
    assert body["cameras"][cam1] == []
    assert body["cameras"][cam2] == []


@pytest.mark.asyncio
async def test_batch_availability_requires_auth(client: AsyncClient):
    now = datetime.now(timezone.utc)
    resp = await client.post(
        "/api/v1/playback/availability/batch",
        json={
            "camera_ids": [],
            "start": (now - timedelta(hours=1)).isoformat(),
            "end": now.isoformat(),
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_timeline_events_empty(client: AsyncClient, auth_headers):
    cam1 = await _create_camera(client, auth_headers, "TimelineCam1")
    now = datetime.now(timezone.utc)

    resp = await client.get(
        "/api/v1/playback/timeline/events",
        params={
            "camera_id": [cam1],
            "start": (now - timedelta(hours=1)).isoformat(),
            "end": now.isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"events": []}
