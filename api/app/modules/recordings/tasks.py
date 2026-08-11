"""
Background asyncio loops that bridge the threaded RecordingManager with
the database. Started/cancelled from main.py's lifespan, following the
same pattern as events/drain_task.py's motion_event_drain_loop.
"""

import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.logging import get_logger
from app.db.session import async_session_factory
from app.modules.cameras.model import Camera
from app.modules.detection.manager import DetectionManager
from app.modules.events.model import Event
from app.modules.realtime.schemas import AlertMessage
from app.modules.recordings.model import Recording
from app.modules.recordings.recording_manager import recording_manager
from app.services.notifications import dispatch_event_alert

logger = get_logger("recordings.tasks")

FLUSH_INTERVAL_SECONDS = 5
RETENTION_INTERVAL_SECONDS = 3600
STATUS_SYNC_INTERVAL_SECONDS = 5


async def start_recording_for_enabled_cameras() -> None:
    """Called once at app startup — starts a recorder thread (and a motion
    detector) for every camera with record_enabled=True."""
    async with async_session_factory() as db:
        result = await db.execute(select(Camera).where(Camera.record_enabled.is_(True)))
        cameras = list(result.scalars().all())

    detection_mgr = DetectionManager.get_instance()
    for camera in cameras:
        detection_mgr.register(str(camera.id))
        recording_manager.start_recording(
            str(camera.id), camera.rtsp_url_encrypted, camera.retention_days
        )
    logger.info("Started recording for %d camera(s)", len(cameras))


async def flush_segments_loop() -> None:
    """Periodically persists completed recording segments to the database."""
    logger.info("Segment flush loop started")
    while True:
        try:
            segments = recording_manager.drain_completed()
            if segments:
                async with async_session_factory() as db:
                    try:
                        for seg in segments:
                            db.add(
                                Recording(
                                    id=seg["id"],
                                    camera_id=seg["camera_id"],
                                    start_time=datetime.fromtimestamp(
                                        seg["start_time"], tz=timezone.utc
                                    ),
                                    end_time=datetime.fromtimestamp(
                                        seg["end_time"], tz=timezone.utc
                                    ),
                                    file_path=seg["file_path"],
                                    file_size=seg["file_size"],
                                    duration_seconds=seg["duration_seconds"],
                                    resolution=seg["resolution"],
                                    status=seg["status"],
                                )
                            )
                        await db.commit()
                        logger.info("Persisted %d recording segment(s)", len(segments))
                    except Exception as exc:
                        await db.rollback()
                        logger.error("Failed to persist segments: %s", exc, exc_info=True)
        except Exception as exc:
            logger.error("Segment flush loop error: %s", exc, exc_info=True)

        await asyncio.sleep(FLUSH_INTERVAL_SECONDS)


async def camera_status_sync_loop() -> None:
    """Applies camera online/offline transitions detected by recorder
    threads to the Camera row, and raises a camera_offline Event so it
    shows up in the activity feed."""
    logger.info("Camera status sync loop started")
    while True:
        try:
            changes = recording_manager.drain_status_changes()
            if changes:
                async with async_session_factory() as db:
                    try:
                        alerts: list[tuple[AlertMessage, Event | None]] = []
                        for camera_id, status in changes:
                            camera = await db.get(Camera, camera_id)
                            if camera is None or camera.status == status:
                                continue
                            camera.status = status
                            now = datetime.now(timezone.utc)
                            if status == "offline":
                                offline_event = Event(
                                    id=uuid.uuid4(),
                                    camera_id=camera_id,
                                    event_type="camera_offline",
                                    subtype=None,
                                    started_at=now,
                                    ended_at=None,
                                    confidence=0.0,
                                    importance="high",
                                    review_status="pending",
                                    metadata_json="{}",
                                )
                                db.add(offline_event)
                                alerts.append(
                                    (
                                        AlertMessage(
                                            event_id=str(offline_event.id),
                                            camera_id=str(camera_id),
                                            camera_name=camera.name,
                                            event_type="camera_offline",
                                            importance="high",
                                            started_at=now.isoformat(),
                                        ),
                                        offline_event,
                                    )
                                )
                            else:
                                alerts.append(
                                    (
                                        AlertMessage(
                                            camera_id=str(camera_id),
                                            camera_name=camera.name,
                                            event_type="camera_online",
                                            importance="low",
                                            started_at=now.isoformat(),
                                        ),
                                        None,
                                    )
                                )
                        await db.commit()

                        # ── Real-time alert fan-out (after commit) ──
                        for alert, related_event in alerts:
                            try:
                                await dispatch_event_alert(db, alert)
                                if related_event is not None:
                                    related_event.alerted = True
                                    await db.commit()
                            except Exception as exc:
                                logger.warning("Failed to dispatch camera status alert: %s", exc)
                    except Exception as exc:
                        await db.rollback()
                        logger.error("Failed to sync camera status: %s", exc, exc_info=True)
        except Exception as exc:
            logger.error("Camera status sync loop error: %s", exc, exc_info=True)

        await asyncio.sleep(STATUS_SYNC_INTERVAL_SECONDS)


async def retention_cleanup_loop() -> None:
    """Periodically purges recordings past their camera's retention window,
    enforces the configured storage cap, and sweeps orphaned files."""
    logger.info("Retention cleanup loop started")
    while True:
        await asyncio.sleep(RETENTION_INTERVAL_SECONDS)
        try:
            async with async_session_factory() as db:
                from app.modules.recordings.service import run_cleanup

                try:
                    result = await run_cleanup(db)
                    await db.commit()
                    logger.info(
                        "Retention cleanup: expired=%d cap=%d orphans=%d empty_dirs=%d",
                        result.expired_deleted,
                        result.cap_deleted,
                        result.orphans_removed,
                        result.empty_dirs_removed,
                    )
                except Exception as exc:
                    await db.rollback()
                    logger.error("Retention cleanup failed: %s", exc, exc_info=True)
        except Exception as exc:
            logger.error("Retention cleanup loop error: %s", exc, exc_info=True)
