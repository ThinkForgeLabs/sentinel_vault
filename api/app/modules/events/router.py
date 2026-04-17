# app/modules/events/router.py
"""
Event endpoints – list, detail, stats, thumbnails, clips.
Windows-safe transcoding via subprocess.run in a thread-pool.
"""

import asyncio
import logging
import shutil
import subprocess
import uuid
from datetime import datetime, date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.events.model import Event
from app.modules.events.schemas import (
    EventResponse,
    EventUpdate,
    EventStats,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["events"])


# ── transcode helper (Windows-safe) ─────────────────────────────────

def _transcode_sync(
    ffmpeg: str, src: str, dest: str
) -> subprocess.CompletedProcess:
    """
    Blocking ffmpeg call – always run via ``run_in_executor`` so the
    event-loop is never blocked and we avoid the Windows
    ``NotImplementedError`` from ``asyncio.create_subprocess_exec``.
    """
    return subprocess.run(
        [
            ffmpeg, "-y",
            "-i", src,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-movflags", "+faststart",
            "-pix_fmt", "yuv420p",
            "-an",
            dest,
        ],
        capture_output=True,
        timeout=300,
    )


async def _ensure_h264(src: Path) -> Path:
    """
    Return a browser-playable H.264 / MP4 path.
    Transcodes once then serves from cache.  Falls back to the original
    file if ffmpeg is missing or fails.
    """
    dest = src.with_suffix(".browser.mp4")
    if dest.exists() and dest.stat().st_size > 0:
        return dest

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        logger.warning("ffmpeg not on PATH – serving original clip")
        return src

    logger.info("Transcoding %s → %s", src.name, dest.name)

    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            None, _transcode_sync, ffmpeg, str(src), str(dest),
        )
    except Exception as exc:
        logger.error("Transcode subprocess error: %s", exc)
        dest.unlink(missing_ok=True)
        return src

    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace")
        logger.error("ffmpeg exit %d: %s", result.returncode, stderr[:500])
        dest.unlink(missing_ok=True)
        return src

    logger.info("Transcode OK: %s (%d bytes)", dest.name, dest.stat().st_size)
    return dest


# ── safe file deletion (Windows-friendly) ────────────────────────────

async def _safe_unlink(path: Path, retries: int = 3, delay: float = 0.5):
    """
    Try to delete a file, retrying on Windows lock errors.
    If still locked after retries, log and move on — retention will
    clean orphans later.
    """
    for attempt in range(retries):
        try:
            if path.exists():
                path.unlink()
            return
        except PermissionError:
            if attempt < retries - 1:
                logger.debug(
                    "File locked (attempt %d/%d), retrying: %s",
                    attempt + 1, retries, path,
                )
                await asyncio.sleep(delay)
            else:
                logger.warning(
                    "Could not delete locked file (will be cleaned by retention): %s",
                    path,
                )
        except OSError as exc:
            logger.warning("Error deleting %s: %s", path, exc)
            return


# ── list events ──────────────────────────────────────────────────────

@router.get("", response_model=list[EventResponse])
async def list_events(
    camera_id: uuid.UUID | None = Query(None),
    event_type: str | None = Query(None),
    importance: str | None = Query(None),
    after: datetime | None = Query(None),
    before: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    q = select(Event).order_by(desc(Event.started_at))

    if camera_id:
        q = q.where(Event.camera_id == camera_id)
    if event_type:
        q = q.where(Event.event_type == event_type)
    if importance:
        q = q.where(Event.importance == importance)
    if after:
        q = q.where(Event.started_at >= after)
    if before:
        q = q.where(Event.started_at <= before)

    q = q.limit(limit).offset(offset)
    result = await db.execute(q)
    return result.scalars().all()


# ── event stats ──────────────────────────────────────────────────────

@router.get("/stats", response_model=EventStats)
async def get_event_stats(
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    today_start = datetime.combine(date.today(), datetime.min.time())

    total_q = select(func.count(Event.id)).where(
        Event.started_at >= today_start
    )
    total_today = (await db.execute(total_q)).scalar() or 0

    type_q = (
        select(Event.event_type, func.count(Event.id))
        .where(Event.started_at >= today_start)
        .group_by(Event.event_type)
    )
    by_type = {r[0]: r[1] for r in (await db.execute(type_q)).all()}

    alert_q = select(func.count(Event.id)).where(
        and_(Event.started_at >= today_start, Event.alerted == True)  # noqa: E712
    )
    alerted_count = (await db.execute(alert_q)).scalar() or 0

    return EventStats(
        total_today=total_today,
        by_type=by_type,
        alerted_count=alerted_count,
    )


# ── single event ─────────────────────────────────────────────────────

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Event not found")
    return event


# ── update event ─────────────────────────────────────────────────────

@router.patch("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: uuid.UUID,
    body: EventUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Event not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(event, field, value)

    await db.commit()
    await db.refresh(event)
    return event


# ── delete event ─────────────────────────────────────────────────────

@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(404, "Event not found")

    # Collect every file we want to remove
    files_to_delete: list[Path] = []
    for attr in ("thumbnail_path", "clip_path"):
        p = getattr(event, attr, None)
        if p:
            path = Path(p)
            files_to_delete.append(path)
            # The transcoded browser copy
            files_to_delete.append(path.with_suffix(".browser.mp4"))

    # Delete DB row FIRST so the event vanishes from the UI immediately
    await db.delete(event)
    await db.commit()

    # Best-effort file cleanup (never fails the request)
    for f in files_to_delete:
        await _safe_unlink(f)


# ── thumbnail ────────────────────────────────────────────────────────

@router.get("/{event_id}/thumbnail")
async def get_event_thumbnail(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event or not event.thumbnail_path:
        raise HTTPException(404, "Thumbnail not found")

    path = Path(event.thumbnail_path)
    if not path.exists():
        raise HTTPException(404, "Thumbnail file missing")

    return FileResponse(path, media_type="image/jpeg")


# ── clip (video) ─────────────────────────────────────────────────────

@router.get("/{event_id}/clip")
async def get_event_clip(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event or not event.clip_path:
        raise HTTPException(404, "Clip not found")

    original = Path(event.clip_path)
    if not original.exists():
        raise HTTPException(404, "Clip file missing")

    h264_path = await _ensure_h264(original)

    return FileResponse(
        h264_path,
        media_type="video/mp4",
        filename=f"event_{event_id}.mp4",
    )