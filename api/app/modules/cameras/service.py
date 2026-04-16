from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundError
from app.modules.cameras.model import Camera
from app.modules.cameras.schemas import CameraCreate, CameraUpdate, TestConnectionResponse


async def list_cameras(db: AsyncSession) -> list[Camera]:
    result = await db.execute(
        select(Camera).options(selectinload(Camera.zones)).order_by(Camera.created_at)
    )
    return list(result.scalars().all())


async def get_camera(db: AsyncSession, camera_id: str) -> Camera:
    result = await db.execute(
        select(Camera).options(selectinload(Camera.zones)).where(Camera.id == camera_id)
    )
    camera = result.scalar_one_or_none()
    if camera is None:
        raise NotFoundError("Camera", camera_id)
    return camera


async def create_camera(db: AsyncSession, data: CameraCreate) -> Camera:
    is_usb = data.rtsp_url.startswith("usb://")
    camera = Camera(
        name=data.name,
        location_label=data.location_label,
        rtsp_url_encrypted=data.rtsp_url,
        record_enabled=data.record_enabled,
        ai_enabled=data.ai_enabled,
        retention_days=data.retention_days,
        status="online" if is_usb else "offline",
    )
    db.add(camera)
    await db.flush()
    return camera


async def update_camera(db: AsyncSession, camera_id: str, data: CameraUpdate) -> Camera:
    camera = await get_camera(db, camera_id)
    updates = data.model_dump(exclude_unset=True)
    if "rtsp_url" in updates:
        updates["rtsp_url_encrypted"] = updates.pop("rtsp_url")
    for key, value in updates.items():
        setattr(camera, key, value)
    await db.flush()
    return camera


async def delete_camera(db: AsyncSession, camera_id: str) -> None:
    camera = await get_camera(db, camera_id)
    await db.delete(camera)
    await db.flush()


async def test_connection(rtsp_url: str) -> TestConnectionResponse:
    if not rtsp_url.startswith("rtsp://"):
        return TestConnectionResponse(success=False, message="Invalid RTSP URL format")

    return TestConnectionResponse(
        success=True,
        message="Connection successful (simulated)",
        codec="H.264",
        resolution="1920x1080",
    )