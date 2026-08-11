import asyncio
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.modules.auth.model import User
from app.modules.playback.schemas import (
    AvailabilityResponse,
    BatchAvailabilityRequest,
    BatchAvailabilityResponse,
    StreamInfo,
    TimelineEventsResponse,
)
from app.modules.playback.service import (
    get_availability,
    get_batch_availability,
    get_stream_info,
    get_timeline_events,
)
from app.modules.recordings.model import Recording

router = APIRouter()


@router.get("/availability", response_model=AvailabilityResponse)
async def playback_availability(
    camera_id: uuid.UUID = Query(...),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await get_availability(db, camera_id, start, end)


@router.post("/availability/batch", response_model=BatchAvailabilityResponse)
async def playback_availability_batch(
    body: BatchAvailabilityRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Multicamera wall view: fetch every tile's availability segments in
    one call so scrubbing stays in sync across cameras."""
    return await get_batch_availability(db, body)


@router.get("/timeline/events", response_model=TimelineEventsResponse)
async def playback_timeline_events(
    camera_id: list[uuid.UUID] = Query(...),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Event markers (motion, camera_offline, etc.) for the Frigate-style
    timeline. Accepts one or more camera_id query params."""
    events = await get_timeline_events(db, camera_id, start, end)
    return TimelineEventsResponse(events=events)


@router.get("/stream/{camera_id}", response_model=StreamInfo)
async def playback_stream(
    camera_id: uuid.UUID,
    _: User = Depends(get_current_user),
):
    return await get_stream_info(camera_id)


# ── Video file serving (with automatic ffmpeg transcode for .avi) ──

def _transcode_to_h264(source: Path, dest: Path) -> None:
    """Blocking call — run inside asyncio.to_thread."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg is not installed.  "
            "Download from https://ffmpeg.org/download.html and add to PATH."
        )
    subprocess.run(
        [
            ffmpeg, "-y",
            "-i", str(source),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-an",                          # webcams rarely have useful audio
            "-movflags", "+faststart",
            "-f", "mp4",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )


@router.get("/recording/{recording_id}/video")
async def serve_recording_video(
    recording_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    recording = await db.get(Recording, recording_id)
    if not recording or not recording.file_path:
        raise HTTPException(status_code=404, detail="Recording not found")

    source = Path(recording.file_path)
    if not source.exists():
        raise HTTPException(status_code=404, detail="Recording file missing from disk")

    # Always serve an H.264 transcode — the original codec is not browser-playable
    transcoded = source.with_name(source.stem + ".h264.mp4")

    if not transcoded.exists():
        try:
            await asyncio.to_thread(_transcode_to_h264, source, transcoded)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else str(exc.stderr)
            raise HTTPException(
                status_code=500,
                detail=f"ffmpeg failed: {stderr[:500]}",
            )

    return FileResponse(transcoded, media_type="video/mp4")