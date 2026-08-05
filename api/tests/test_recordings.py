import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recordings.model import Recording


async def _create_camera(client: AsyncClient, auth_headers: dict) -> str:
    resp = await client.post(
        "/api/v1/cameras",
        json={"name": "Rec Cam", "rtsp_url": "rtsp://10.0.0.9/stream"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _insert_recording(db_session: AsyncSession, camera_id: str, tmp_path) -> Recording:
    file_path = tmp_path / "segment.avi"
    file_path.write_bytes(b"fake-avi-bytes")

    start = datetime.now(timezone.utc) - timedelta(minutes=15)
    end = datetime.now(timezone.utc)
    recording = Recording(
        id=uuid.uuid4(),
        camera_id=uuid.UUID(camera_id),
        start_time=start,
        end_time=end,
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
        duration_seconds=900.0,
        resolution="1280x720",
        status="complete",
    )
    db_session.add(recording)
    await db_session.commit()
    return recording


@pytest.mark.asyncio
async def test_list_recordings(client: AsyncClient, auth_headers, db_session, tmp_path):
    camera_id = await _create_camera(client, auth_headers)
    await _insert_recording(db_session, camera_id, tmp_path)

    resp = await client.get("/api/v1/recordings", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["camera_id"] == camera_id
    assert data[0]["status"] == "complete"

    filtered = await client.get(
        "/api/v1/recordings", params={"camera_id": camera_id}, headers=auth_headers
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1


@pytest.mark.asyncio
async def test_get_and_delete_recording(client: AsyncClient, auth_headers, db_session, tmp_path):
    camera_id = await _create_camera(client, auth_headers)
    recording = await _insert_recording(db_session, camera_id, tmp_path)
    recording_id = str(recording.id)

    get_resp = await client.get(f"/api/v1/recordings/{recording_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == recording_id

    download_resp = await client.get(
        f"/api/v1/recordings/{recording_id}/download", headers=auth_headers
    )
    assert download_resp.status_code == 200
    assert download_resp.content == b"fake-avi-bytes"

    delete_resp = await client.delete(f"/api/v1/recordings/{recording_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    missing_resp = await client.get(f"/api/v1/recordings/{recording_id}", headers=auth_headers)
    assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_storage_stats(client: AsyncClient, auth_headers, db_session, tmp_path):
    camera_id = await _create_camera(client, auth_headers)
    await _insert_recording(db_session, camera_id, tmp_path)

    resp = await client.get("/api/v1/recordings/storage", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["recordings_count"] == 1
    assert data["recordings_total_bytes"] > 0


@pytest.mark.asyncio
async def test_storage_settings_roundtrip(client: AsyncClient, auth_headers):
    put_resp = await client.put(
        "/api/v1/recordings/storage/settings",
        json={"max_storage_gb": 100, "storage_warning_percent": 85},
        headers=auth_headers,
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["max_storage_gb"] == 100
    assert put_resp.json()["storage_warning_percent"] == 85

    get_resp = await client.get("/api/v1/recordings/storage/settings", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["max_storage_gb"] == 100
