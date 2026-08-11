import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine, async_session_factory
from app.db.base import Base
from app.middleware.error_handler import register_error_handlers
from app.middleware.request_context import RequestContextMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router
from app.modules.cameras.router import router as cameras_router
from app.modules.cameras.capture_manager import capture_manager
from app.modules.events.router import router as events_router
from app.modules.playback.router import router as playback_router
from app.modules.settings.router import router as settings_router
from app.modules.recordings.router import router as recordings_router
from app.modules.recordings.recording_manager import recording_manager
from app.modules.recordings.tasks import (
    camera_status_sync_loop,
    flush_segments_loop,
    retention_cleanup_loop,
    start_recording_for_enabled_cameras,
)
from app.modules.detection.routes import router as detection_router
from app.modules.detection.service import init_detectors
from app.modules.events.drain_task import motion_event_drain_loop
from app.modules.realtime.router import router as realtime_router

logger = logging.getLogger(__name__)


async def _cancel_task(task: asyncio.Task, name: str):
    """Cancel a background task and suppress CancelledError."""
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info(f"Shutdown: cancelled {name}")


async def _final_flush_segments():
    """Persist any recording segments still in the queue."""
    from app.modules.recordings.model import Recording

    segments = recording_manager.drain_completed()
    if not segments:
        return
    try:
        async with async_session_factory() as db:
            for seg in segments:
                db.add(Recording(
                    id=seg["id"],
                    camera_id=seg["camera_id"],
                    start_time=seg["start_time"],
                    end_time=seg["end_time"],
                    file_path=seg["file_path"],
                    file_size=seg["file_size"],
                    duration_seconds=seg["duration_seconds"],
                    resolution=seg["resolution"],
                    status=seg["status"],
                ))
            await db.commit()
        logger.info(f"Shutdown: flushed {len(segments)} final segments")
    except Exception as e:
        logger.warning(f"Shutdown: segment flush failed: {e}")


async def _final_flush_events():
    """Persist any motion events still in the queue."""
    import json

    from app.modules.events.model import Event

    events = recording_manager.drain_motion_events()
    if not events:
        return
    try:
        async with async_session_factory() as db:
            for ev in events:
                clip_duration = ev.get("clip_duration_seconds")
                db.add(Event(
                    id=ev["id"],
                    camera_id=ev["camera_id"],
                    event_type=ev.get("event_type", "motion"),
                    subtype=ev.get("subtype", "frame_diff"),
                    started_at=ev["started_at"],
                    ended_at=ev["ended_at"],
                    confidence=ev["confidence"],
                    importance=ev["importance"],
                    thumbnail_path=ev.get("thumbnail_path"),
                    clip_path=ev.get("clip_path"),
                    clip_duration_seconds=round(clip_duration) if clip_duration is not None else None,
                    metadata_json=json.dumps(ev.get("metadata", {})),
                ))
            await db.commit()
        logger.info(f"Shutdown: flushed {len(events)} final events")
    except Exception as e:
        logger.warning(f"Shutdown: event flush failed: {e}")


PLACEHOLDER_SECRET_KEY = "change-me-to-a-random-64-char-string"


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    if settings.environment != "development" and settings.secret_key == PLACEHOLDER_SECRET_KEY:
        raise RuntimeError(
            "Refusing to start: SECRET_KEY is still the placeholder value. "
            "Set a real random SECRET_KEY in the environment before running "
            "outside of development."
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ── Recording startup ──
    await start_recording_for_enabled_cameras()
    task_flush = asyncio.create_task(flush_segments_loop())
    task_retention = asyncio.create_task(retention_cleanup_loop())
    task_status_sync = asyncio.create_task(camera_status_sync_loop())

    # ── Detection startup ──
    async with async_session_factory() as db:
        from app.modules.cameras.model import Camera
        from sqlalchemy import select
        result = await db.execute(select(Camera.id))
        camera_ids = [str(row[0]) for row in result.all()]
        await init_detectors(db, camera_ids)

    task_motion_drain = asyncio.create_task(motion_event_drain_loop())

    yield

    # ──────────────────────────────────────
    #  Shutdown  (order matters!)
    # ──────────────────────────────────────

    logger.info("Shutdown: stopping recordings...")

    # 1. Signal all recording threads to stop
    recording_manager.stop_all()

    # 2. Wait for threads to finish writing final segments / clips
    await asyncio.to_thread(recording_manager.wait_for_threads, 15)

    # 3. Final DB flush for anything the threads enqueued during wind-down
    await _final_flush_segments()
    await _final_flush_events()

    # 4. Cancel background loop tasks (nothing left to flush)
    await _cancel_task(task_flush, "flush_segments_loop")
    await _cancel_task(task_retention, "retention_cleanup_loop")
    await _cancel_task(task_status_sync, "camera_status_sync_loop")
    await _cancel_task(task_motion_drain, "motion_event_drain_loop")

    # 5. Release camera hardware
    capture_manager.release_all()

    # 6. Dispose DB engine
    await engine.dispose()

    logger.info("Shutdown: complete")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# ── Middleware ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)

register_error_handlers(app)

# ── Routes ──
PREFIX = settings.api_prefix

app.include_router(auth_router, prefix=f"{PREFIX}/auth", tags=["Auth"])
app.include_router(users_router, prefix=f"{PREFIX}/users", tags=["Users"])
app.include_router(cameras_router, prefix=f"{PREFIX}/cameras", tags=["Cameras"])
app.include_router(events_router, prefix=f"{PREFIX}/events", tags=["Events"])
app.include_router(playback_router, prefix=f"{PREFIX}/playback", tags=["Playback"])
app.include_router(settings_router, prefix=f"{PREFIX}/settings", tags=["Settings"])
app.include_router(recordings_router, prefix=f"{PREFIX}/recordings", tags=["Recordings"])
app.include_router(detection_router, prefix=f"{PREFIX}/detection", tags=["Detection"])
app.include_router(realtime_router, prefix=f"{PREFIX}/realtime", tags=["Realtime"])


@app.get(f"{PREFIX}/system/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}