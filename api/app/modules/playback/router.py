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
from app.modules.playback.schemas import AvailabilityResponse, StreamInfo
from app.modules.playback.service import get_availability, get_stream_info
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