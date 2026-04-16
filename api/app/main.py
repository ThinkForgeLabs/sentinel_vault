import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import setup_logging
from app.db.session import engine
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
from app.modules.recordings.routes import router as recordings_router
from app.modules.recordings.recording_manager import recording_manager
from app.modules.recordings.tasks import (
    flush_segments_loop,
    retention_cleanup_loop,
    start_recording_for_enabled_cameras,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ── Recording startup ──
    await start_recording_for_enabled_cameras()
    task_flush = asyncio.create_task(flush_segments_loop())
    task_retention = asyncio.create_task(retention_cleanup_loop())

    yield

    # ── Shutdown ──
    task_flush.cancel()
    task_retention.cancel()
    recording_manager.stop_all()
    capture_manager.release_all()
    await engine.dispose()


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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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


@app.get(f"{PREFIX}/system/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}