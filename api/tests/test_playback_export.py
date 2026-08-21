import shutil
import subprocess
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.recordings.model import Recording


def _make_test_video(path, duration_seconds: float) -> None:
    """Generate a tiny real H.264 MP4 via ffmpeg's testsrc so the export
    endpoint has something real to trim/transcode/concat — fake bytes
    would make ffmpeg fail immediately."""
    ffmpeg = shutil.which("ffmpeg")
    assert ffmpeg, "ffmpeg must be installed for this test"
    subprocess.run(
        [
            ffmpeg, "-y",
            "-f", "lavfi",
            "-i", f"testsrc=duration={duration_seconds}:size=320x240:rate=10",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            str(path),
        ],
        check=True,
        capture_output=True,
    )


async def _create_camera(client: AsyncClient, auth_headers: dict, name: str = "Export Cam") -> str:
    resp = await client.post(
        "/api/v1/cameras",
        json={"name": name, "rtsp_url": "rtsp://10.0.0.9/stream"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _insert_recording(
    db_session: AsyncSession,
    camera_id: str,
    tmp_path,
    *,
    start: datetime,
    duration_seconds: float,
    name: str = "segment.mp4",
) -> Recording:
    file_path = tmp_path / name
    _make_test_video(file_path, duration_seconds)

    recording = Recording(
        id=uuid.uuid4(),
        camera_id=uuid.UUID(camera_id),
        start_time=start,
        end_time=start + timedelta(seconds=duration_seconds),
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
        duration_seconds=duration_seconds,
        resolution="320x240",
        status="complete",
    )
    db_session.add(recording)
    await db_session.commit()
    return recording


@pytest.mark.asyncio
async def test_export_single_segment(client: AsyncClient, auth_headers, db_session, tmp_path):
    camera_id = await _create_camera(client, auth_headers)
    base = datetime.now(timezone.utc) - timedelta(minutes=10)
    await _insert_recording(db_session, camera_id, tmp_path, start=base, duration_seconds=6.0)

    resp = await client.get(
        "/api/v1/playback/export",
        params={
            "camera_id": camera_id,
            "start": (base + timedelta(seconds=1)).isoformat(),
            "end": (base + timedelta(seconds=4)).isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("video/mp4")
    assert "attachment" in resp.headers["content-disposition"]
    assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_export_spanning_two_segments(client: AsyncClient, auth_headers, db_session, tmp_path):
    camera_id = await _create_camera(client, auth_headers, "Export Cam 2")
    base = datetime.now(timezone.utc) - timedelta(minutes=10)

    await _insert_recording(
        db_session, camera_id, tmp_path, start=base, duration_seconds=5.0, name="seg1.mp4"
    )
    await _insert_recording(
        db_session,
        camera_id,
        tmp_path,
        start=base + timedelta(seconds=5),
        duration_seconds=5.0,
        name="seg2.mp4",
    )

    resp = await client.get(
        "/api/v1/playback/export",
        params={
            "camera_id": camera_id,
            "start": (base + timedelta(seconds=3)).isoformat(),
            "end": (base + timedelta(seconds=7)).isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("video/mp4")
    assert len(resp.content) > 0


@pytest.mark.asyncio
async def test_export_no_recordings_returns_404(client: AsyncClient, auth_headers):
    camera_id = await _create_camera(client, auth_headers, "Empty Cam")
    now = datetime.now(timezone.utc)

    resp = await client.get(
        "/api/v1/playback/export",
        params={
            "camera_id": camera_id,
            "start": (now - timedelta(minutes=5)).isoformat(),
            "end": now.isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_rejects_end_before_start(client: AsyncClient, auth_headers):
    camera_id = await _create_camera(client, auth_headers, "Bad Range Cam")
    now = datetime.now(timezone.utc)

    resp = await client.get(
        "/api/v1/playback/export",
        params={
            "camera_id": camera_id,
            "start": now.isoformat(),
            "end": (now - timedelta(minutes=5)).isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_export_rejects_too_long_range(client: AsyncClient, auth_headers):
    camera_id = await _create_camera(client, auth_headers, "Too Long Cam")
    now = datetime.now(timezone.utc)

    resp = await client.get(
        "/api/v1/playback/export",
        params={
            "camera_id": camera_id,
            "start": (now - timedelta(hours=5)).isoformat(),
            "end": now.isoformat(),
        },
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_export_requires_auth(client: AsyncClient):
    now = datetime.now(timezone.utc)
    resp = await client.get(
        "/api/v1/playback/export",
        params={
            "camera_id": str(uuid.uuid4()),
            "start": (now - timedelta(minutes=5)).isoformat(),
            "end": now.isoformat(),
        },
    )
    assert resp.status_code == 401
