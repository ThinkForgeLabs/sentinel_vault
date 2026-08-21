import asyncio
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crypto
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.modules.auth.model import User
from app.modules.cameras.model import Camera
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
    get_export_recordings,
    get_stream_info,
    get_timeline_events,
)
from app.modules.recordings.model import Recording
from app.services.video_crypto import cleanup_task, ensure_playable_encrypted

router = APIRouter()

# Hard cap on a single exported clip's duration — keeps ffmpeg export work
# (which runs synchronously in a thread, decrypting + transcoding every
# overlapping segment) bounded and prevents a giant range from tying up
# the worker or filling disk with temp files.
EXPORT_MAX_SECONDS = 2 * 60 * 60


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

def _transcode_to_h264(source: str, dest: str) -> None:
    """Blocking call — run inside asyncio.to_thread. `source`/`dest` are
    plain (already-decrypted) temp file paths handed to us by
    ensure_playable_encrypted; the encrypted original never touches
    ffmpeg directly."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg is not installed.  "
            "Download from https://ffmpeg.org/download.html and add to PATH."
        )
    subprocess.run(
        [
            ffmpeg, "-y",
            "-i", source,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-an",                          # webcams rarely have useful audio
            "-movflags", "+faststart",
            "-f", "mp4",
            dest,
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

    # Always serve an H.264 transcode — the original codec is not
    # browser-playable. The recording on disk is encrypted at rest, so
    # transcoding happens against a temp decrypted copy, and the cached
    # transcode output is re-encrypted before being written to disk.
    cache_path = source.with_name(source.stem + ".h264.mp4")

    try:
        temp_path = await ensure_playable_encrypted(source, cache_path, _transcode_to_h264)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else str(exc.stderr)
        raise HTTPException(
            status_code=500,
            detail=f"ffmpeg failed: {stderr[:500]}",
        )

    return FileResponse(temp_path, media_type="video/mp4", background=cleanup_task(temp_path))


# ── Arbitrary time-range export (Frigate-style "select on timeline, ──
# ── download a clip") — distinct from the auto-detected motion clips ──
# ── served at /events/{id}/clip.                                     ──

def _run_ffmpeg(args: list[str]) -> None:
    subprocess.run(args, check=True, capture_output=True)


def _require_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError(
            "ffmpeg is not installed.  "
            "Download from https://ffmpeg.org/download.html and add to PATH."
        )
    return ffmpeg


def _trim_segment(source: str, dest: str, offset_seconds: float, duration_seconds: float) -> None:
    """Blocking. Cut [offset, offset+duration] out of `source` and
    transcode to H.264/MP4 at `dest` — same encode settings as
    _transcode_to_h264 so segments concatenate cleanly."""
    ffmpeg = _require_ffmpeg()
    _run_ffmpeg(
        [
            ffmpeg, "-y",
            "-ss", f"{max(offset_seconds, 0):.3f}",
            "-i", source,
            "-t", f"{max(duration_seconds, 0):.3f}",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-an",
            "-movflags", "+faststart",
            "-f", "mp4",
            dest,
        ]
    )


def _concat_segments(segment_paths: list[str], dest: str) -> None:
    """Blocking. Stitch already-trimmed, identically-encoded MP4 segments
    into one file via the ffmpeg concat demuxer (stream copy — no
    re-encode needed since every segment came out of _trim_segment)."""
    ffmpeg = _require_ffmpeg()
    fd, list_path = tempfile.mkstemp(suffix=".txt")
    try:
        with os.fdopen(fd, "w") as f:
            for p in segment_paths:
                f.write(f"file '{p}'\n")
        _run_ffmpeg([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", dest])
    finally:
        os.unlink(list_path)


def _build_export(overlaps: list[tuple[Recording, float, float]]) -> Path:
    """Blocking. For each overlapping recording: decrypt to a temp
    plaintext copy, trim to just the requested slice, transcode to
    H.264/MP4. If more than one segment is involved, concat them into a
    single output file. Returns the path to the final (plaintext, not
    yet sent) MP4 — caller is responsible for cleaning it up."""
    trimmed_paths: list[Path] = []
    try:
        for rec, offset, duration in overlaps:
            src_path = Path(rec.file_path)
            with crypto.decrypted_temp_copy(src_path, suffix=src_path.suffix) as plain_src:
                fd, tmp_name = tempfile.mkstemp(suffix=".mp4")
                os.close(fd)
                _trim_segment(str(plain_src), tmp_name, offset, duration)
                trimmed_paths.append(Path(tmp_name))

        if len(trimmed_paths) == 1:
            fd, final_name = tempfile.mkstemp(suffix=".mp4")
            os.close(fd)
            os.replace(trimmed_paths[0], final_name)
            trimmed_paths.clear()
            return Path(final_name)

        fd, final_name = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)
        _concat_segments([str(p) for p in trimmed_paths], final_name)
        return Path(final_name)
    finally:
        for p in trimmed_paths:
            p.unlink(missing_ok=True)


@router.get("/export")
async def export_clip(
    camera_id: uuid.UUID = Query(...),
    start: datetime = Query(...),
    end: datetime = Query(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Export an arbitrary time range the user selects on the Playback
    timeline as a single downloadable MP4, stitched from whichever
    recording segments overlap the range. Separate from the
    auto-detected motion clips at /events/{id}/clip."""
    # Same naive/aware normalization as the recording timestamps below —
    # a client-supplied ISO string without an offset is treated as UTC.
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)

    if end <= start:
        raise HTTPException(status_code=400, detail="end must be after start")
    if (end - start).total_seconds() > EXPORT_MAX_SECONDS:
        raise HTTPException(
            status_code=400,
            detail=f"Export range too long (max {EXPORT_MAX_SECONDS // 60} minutes)",
        )

    camera = await db.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    recordings = await get_export_recordings(db, camera_id, start, end)

    overlaps: list[tuple[Recording, float, float]] = []
    for rec in recordings:
        # SQLite doesn't round-trip tzinfo, so a value written as
        # timezone-aware can come back naive. Treat naive DB timestamps
        # as UTC (everything in this app is stored/compared in UTC) so
        # Python's datetime comparisons below don't blow up.
        rec_start = rec.start_time if rec.start_time.tzinfo else rec.start_time.replace(tzinfo=timezone.utc)
        rec_end = rec.end_time if rec.end_time.tzinfo else rec.end_time.replace(tzinfo=timezone.utc)
        overlap_start = max(start, rec_start)
        overlap_end = min(end, rec_end)
        if overlap_start < overlap_end:
            offset = (overlap_start - rec_start).total_seconds()
            duration = (overlap_end - overlap_start).total_seconds()
            overlaps.append((rec, offset, duration))

    if not overlaps:
        raise HTTPException(status_code=404, detail="No recordings found for the given range")

    try:
        output_path = await asyncio.to_thread(_build_export, overlaps)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else str(exc.stderr)
        raise HTTPException(status_code=500, detail=f"ffmpeg failed: {stderr[:500]}")

    safe_name = "".join(c if c.isalnum() else "_" for c in camera.name) or "camera"
    filename = f"{safe_name}_{start.strftime('%Y%m%dT%H%M%S')}_{end.strftime('%Y%m%dT%H%M%S')}.mp4"

    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=filename,
        background=cleanup_task(output_path),
    )