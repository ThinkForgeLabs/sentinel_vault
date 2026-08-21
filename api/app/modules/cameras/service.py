import uuid

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core import crypto
from app.core.exceptions import NotFoundError
from app.modules.cameras.model import Camera
from app.modules.cameras.schemas import CameraCreate, CameraUpdate, TestConnectionResponse
from app.services.audit import log_action


async def list_cameras(db: AsyncSession) -> list[Camera]:
    result = await db.execute(
        select(Camera).options(selectinload(Camera.zones)).order_by(Camera.created_at)
    )
    return list(result.scalars().all())


async def get_camera(db: AsyncSession, camera_id: uuid.UUID) -> Camera:
    result = await db.execute(
        select(Camera).options(selectinload(Camera.zones)).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    if camera is None:
        raise NotFoundError("Camera", camera_id)
    return camera


async def create_camera(
    db: AsyncSession, data: CameraCreate, actor_id: str | None = None
) -> Camera:
    is_usb = data.rtsp_url.startswith("usb://")
    camera = Camera(
        name=data.name,
        location_label=data.location_label,
        rtsp_url_encrypted=crypto.encrypt_str(data.rtsp_url),
        record_enabled=data.record_enabled,
        retention_days=data.retention_days,
        status="online" if is_usb else "offline",
    )
    db.add(camera)
    await db.flush()

    from app.modules.detection.manager import DetectionManager
    DetectionManager.get_instance().register(str(camera.id))

    if camera.record_enabled:
        from app.modules.recordings.recording_manager import recording_manager
        recording_manager.start_recording(
            str(camera.id), crypto.decrypt_str(camera.rtsp_url_encrypted), camera.retention_days
        )

    await log_action(
        db,
        actor_id=actor_id,
        action="create_camera",
        resource_type="camera",
        resource_id=str(camera.id),
        details={"name": camera.name, "location_label": camera.location_label},
    )

    return camera


async def update_camera(
    db: AsyncSession, camera_id: uuid.UUID, data: CameraUpdate, actor_id: str | None = None
) -> Camera:
    camera = await get_camera(db, camera_id)
    updates = data.model_dump(exclude_unset=True)

    needs_restart = "rtsp_url" in updates or "retention_days" in updates

    if "rtsp_url" in updates:
        updates["rtsp_url_encrypted"] = crypto.encrypt_str(updates.pop("rtsp_url"))
    for key, value in updates.items():
        setattr(camera, key, value)
    await db.flush()

    from app.modules.recordings.recording_manager import recording_manager

    if not camera.record_enabled:
        recording_manager.stop_recording(str(camera.id))
    elif "record_enabled" in updates or needs_restart:
        # (Re)start with the latest source/retention. start_recording is a
        # no-op if already running with the same camera_id, so stop first
        # whenever the source or retention window may have changed.
        recording_manager.stop_recording(str(camera.id))
        recording_manager.start_recording(
            str(camera.id), crypto.decrypt_str(camera.rtsp_url_encrypted), camera.retention_days
        )

    # Never log the raw RTSP URL/credentials — only which fields changed.
    await log_action(
        db,
        actor_id=actor_id,
        action="update_camera",
        resource_type="camera",
        resource_id=str(camera_id),
        details={"fields": list(updates.keys())},
    )

    return camera


async def delete_camera(
    db: AsyncSession, camera_id: uuid.UUID, actor_id: str | None = None
) -> None:
    camera = await get_camera(db, camera_id)
    camera_name = camera.name

    # Stop recording and detection before deleting
    from app.modules.recordings.recording_manager import recording_manager
    recording_manager.stop_recording(str(camera.id))

    from app.modules.detection.manager import DetectionManager
    detection_mgr = DetectionManager.get_instance()
    detection_mgr.unregister(str(camera.id))

    cam_id = camera.id

    # Bulk-delete all child rows that have NOT NULL FK to cameras.
    # The ORM's backref="recordings" causes SQLAlchemy to try SET NULL
    # at the Python level before SQL reaches the DB, violating NOT NULL.
    # Bulk deletes bypass the ORM identity map and go straight to SQL.
    from app.modules.events.model import Event
    from app.modules.recordings.model import Recording

    await db.execute(sa_delete(Event).where(Event.camera_id == cam_id))
    await db.execute(sa_delete(Recording).where(Recording.camera_id == cam_id))

    await db.delete(camera)
    await db.flush()

    await log_action(
        db,
        actor_id=actor_id,
        action="delete_camera",
        resource_type="camera",
        resource_id=str(cam_id),
        details={"name": camera_name},
    )


async def test_connection(rtsp_url: str) -> TestConnectionResponse:
    if not rtsp_url.startswith("rtsp://"):
        return TestConnectionResponse(success=False, message="Invalid RTSP URL format")

    return TestConnectionResponse(
        success=True,
        message="Connection successful (simulated)",
        codec="H.264",
        resolution="1920x1080",
    )