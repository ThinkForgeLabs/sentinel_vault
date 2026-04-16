from fastapi import APIRouter, Depends
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.modules.auth.model import User
from .manager import DetectionManager
from .schemas import MotionSettingsRead, MotionSettingsUpdate, MotionStatusRead
from . import service

router = APIRouter()


@router.get("/{camera_id}/settings", response_model=MotionSettingsRead)
async def read_motion_settings(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.get_motion_settings(db, camera_id)


@router.put("/{camera_id}/settings", response_model=MotionSettingsRead)
async def write_motion_settings(
    camera_id: UUID,
    body: MotionSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.update_motion_settings(db, camera_id, body)


@router.get("/{camera_id}/status", response_model=MotionStatusRead)
async def read_motion_status(
    camera_id: UUID,
    _: User = Depends(get_current_user),
):
    mgr = DetectionManager.get_instance()
    detector = mgr.get_detector(str(camera_id))

    if detector is None:
        return MotionStatusRead(
            camera_id=camera_id,
            detector_active=False,
            enabled=False,
            frames_processed=0,
        )

    last_trigger = None
    if detector.last_trigger_time > 0:
        last_trigger = datetime.fromtimestamp(
            detector.last_trigger_time, tz=timezone.utc
        )

    return MotionStatusRead(
        camera_id=camera_id,
        detector_active=True,
        enabled=detector.enabled,
        frames_processed=detector.frames_processed,
        last_trigger=last_trigger,
    )