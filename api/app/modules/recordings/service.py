import asyncio
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.modules.cameras.model import Camera
from app.modules.recordings.model import Recording
from app.modules.recordings.schemas import (
    CameraBreakdown,
    CleanupResult,
    RecordingFilters,
    StorageSettingsPayload,
    StorageStats,
)
from app.modules.settings.service import get_setting, upsert_setting
from app.modules.settings.schemas import SettingUpdate

logger = get_logger("recordings")

STORAGE_SETTINGS_KEY = "storage_settings"
DEFAULT_STORAGE_SETTINGS = {"max_storage_gb": None, "storage_warning_percent": 90}


# ── CRUD ──


async def list_recordings(
    db: AsyncSession, filters: RecordingFilters, offset: int = 0, limit: int = 50
) -> list[Recording]:
    stmt = select(Recording).order_by(Recording.start_time.desc())

    if filters.camera_id:
        stmt = stmt.where(Recording.camera_id == filters.camera_id)
    if filters.status:
        stmt = stmt.where(Recording.status == filters.status)
    if filters.after:
        stmt = stmt.where(Recording.start_time >= filters.after)
    if filters.before:
        stmt = stmt.where(Recording.start_time <= filters.before)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_recording(db: AsyncSession, recording_id: UUID) -> Recording:
    recording = await db.get(Recording, recording_id)
    if recording is None:
        raise NotFoundError("Recording", str(recording_id))
    return recording


async def _safe_unlink(path: Path, retries: int = 3, delay: float = 0.5) -> None:
    """Delete a file, retrying on Windows file-lock errors (a recorder
    thread may still hold the segment open). Mirrors the pattern used in
    events/router.py's clip cleanup."""
    for attempt in range(retries):
        try:
            if path.exists():
                path.unlink()
            return
        except PermissionError:
            if attempt < retries - 1:
                await asyncio.sleep(delay)
            else:
                logger.warning("Could not delete locked file (will retry on next cleanup): %s", path)
        except OSError as exc:
            logger.warning("Error deleting %s: %s", path, exc)
            return


async def _unlink_recording_files(file_path: str) -> None:
    """Best-effort removal of a recording's original file and its cached
    browser-transcoded copy (created on demand by the playback module)."""
    if not file_path:
        return
    path = Path(file_path)
    await _safe_unlink(path)
    await _safe_unlink(path.with_name(path.stem + ".h264.mp4"))


async def delete_recording(db: AsyncSession, recording_id: UUID) -> None:
    recording = await get_recording(db, recording_id)
    await _unlink_recording_files(recording.file_path)
    await db.delete(recording)
    await db.flush()


# ── Storage settings ──


async def get_storage_settings(db: AsyncSession) -> StorageSettingsPayload:
    raw = await get_setting(db, STORAGE_SETTINGS_KEY)
    data = json.loads(raw.value_json) if raw else DEFAULT_STORAGE_SETTINGS.copy()
    return StorageSettingsPayload(**{**DEFAULT_STORAGE_SETTINGS, **data})


async def update_storage_settings(
    db: AsyncSession, data: StorageSettingsPayload
) -> StorageSettingsPayload:
    await upsert_setting(
        db, STORAGE_SETTINGS_KEY, SettingUpdate(value_json=json.dumps(data.model_dump()))
    )
    await db.flush()
    return data


# ── Storage stats ──


async def get_storage_stats(db: AsyncSession) -> StorageStats:
    storage_settings = await get_storage_settings(db)

    Path(settings.storage_root).mkdir(parents=True, exist_ok=True)
    disk_total, disk_used, disk_free = shutil.disk_usage(settings.storage_root)
    disk_pct = round((disk_used / disk_total) * 100, 1) if disk_total else 0.0

    totals_result = await db.execute(
        select(
            func.count(Recording.id),
            func.coalesce(func.sum(Recording.file_size), 0),
            func.coalesce(func.sum(Recording.duration_seconds), 0.0),
        )
    )
    rec_count, rec_bytes, rec_duration = totals_result.one()

    per_camera_result = await db.execute(
        select(
            Camera.id,
            Camera.name,
            Camera.retention_days,
            func.count(Recording.id),
            func.coalesce(func.sum(Recording.file_size), 0),
        )
        .outerjoin(Recording, Recording.camera_id == Camera.id)
        .group_by(Camera.id, Camera.name, Camera.retention_days)
        .order_by(Camera.name)
    )
    per_camera = [
        CameraBreakdown(
            camera_id=str(cam_id),
            camera_name=name,
            retention_days=retention_days,
            recording_count=count,
            size_bytes=size,
        )
        for cam_id, name, retention_days, count, size in per_camera_result.all()
    ]

    max_bytes = (
        storage_settings.max_storage_gb * (1024**3) if storage_settings.max_storage_gb else None
    )
    if max_bytes:
        warning_active = (rec_bytes / max_bytes) * 100 >= storage_settings.storage_warning_percent
    else:
        warning_active = disk_pct >= storage_settings.storage_warning_percent

    return StorageStats(
        disk_total_bytes=disk_total,
        disk_used_bytes=disk_used,
        disk_free_bytes=disk_free,
        disk_usage_percent=disk_pct,
        recordings_total_bytes=int(rec_bytes),
        recordings_count=int(rec_count),
        recordings_total_duration_seconds=float(rec_duration),
        max_storage_gb=storage_settings.max_storage_gb,
        storage_warning_percent=storage_settings.storage_warning_percent,
        storage_warning_active=warning_active,
        per_camera=per_camera,
    )


# ── Cleanup ──


async def run_cleanup(db: AsyncSession) -> CleanupResult:
    expired_deleted = await _delete_expired(db)
    cap_deleted = await _delete_over_cap(db)
    orphans_removed = await _remove_orphan_files(db)
    empty_dirs_removed = _remove_empty_dirs()
    await db.flush()
    return CleanupResult(
        expired_deleted=expired_deleted,
        cap_deleted=cap_deleted,
        orphans_removed=orphans_removed,
        empty_dirs_removed=empty_dirs_removed,
    )


async def _delete_expired(db: AsyncSession) -> int:
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(Recording, Camera.retention_days)
        .join(Camera, Camera.id == Recording.camera_id)
    )
    deleted = 0
    for recording, retention_days in result.all():
        cutoff = now - timedelta(days=retention_days)
        if recording.end_time.replace(tzinfo=recording.end_time.tzinfo or timezone.utc) < cutoff:
            await _unlink_recording_files(recording.file_path)
            await db.delete(recording)
            deleted += 1
    return deleted


async def _delete_over_cap(db: AsyncSession) -> int:
    storage_settings = await get_storage_settings(db)
    if not storage_settings.max_storage_gb:
        return 0

    max_bytes = storage_settings.max_storage_gb * (1024**3)
    result = await db.execute(
        select(Recording)
        .where(Recording.status == "complete")
        .order_by(Recording.start_time.asc())
    )
    recordings = list(result.scalars().all())
    total = sum(r.file_size for r in recordings)

    deleted = 0
    for recording in recordings:
        if total <= max_bytes:
            break
        total -= recording.file_size
        await _unlink_recording_files(recording.file_path)
        await db.delete(recording)
        deleted += 1
    return deleted


async def _remove_orphan_files(db: AsyncSession) -> int:
    """Delete files on disk that no longer have a matching Recording row.
    Skips the shared clips/thumbnails directories (owned by the events
    module) and derived browser-transcode caches of files that are still
    tracked."""
    root = Path(settings.storage_root)
    if not root.exists():
        return 0

    result = await db.execute(select(Recording.file_path))
    known_paths = {str(Path(p).resolve()) for (p,) in result.all() if p}

    removed = 0
    for camera_dir in root.iterdir():
        if not camera_dir.is_dir() or camera_dir.name in ("clips", "thumbnails"):
            continue
        for f in camera_dir.iterdir():
            if not f.is_file():
                continue
            resolved = str(f.resolve())
            if resolved in known_paths:
                continue
            if f.name.endswith(".h264.mp4"):
                base = f.with_name(f.name[: -len(".h264.mp4")])
                if str(base.resolve()) in known_paths:
                    continue
            try:
                f.unlink()
                removed += 1
            except OSError:
                pass
    return removed


def _remove_empty_dirs() -> int:
    root = Path(settings.storage_root)
    if not root.exists():
        return 0

    removed = 0
    for camera_dir in root.iterdir():
        if camera_dir.is_dir() and camera_dir.name not in ("clips", "thumbnails"):
            try:
                if not any(camera_dir.iterdir()):
                    camera_dir.rmdir()
                    removed += 1
            except OSError:
                pass
    return removed
