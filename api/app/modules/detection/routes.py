from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.modules.auth.model import User

from . import service
from .manager import DetectionManager
from .schemas import (
    DetectionEngineStatus,
    DetectionSettingsRead,
    DetectionSettingsUpdate,
    MotionSettingsRead,
    MotionSettingsUpdate,
    MotionStatusRead,
)

router = APIRouter()


# NOTE: registered before the /{camera_id}/... routes below — Starlette
# matches routes by structural position (2 path segments here, same as
# /{camera_id}/status), so this must come first or "/engine/status" would
# be captured as camera_id="engine" and fail UUID validation with a 422.
@router.get("/engine/status", response_model=list[DetectionEngineStatus])
async def read_engine_status(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.get_engine_status(db)


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


@router.get("/{camera_id}/detection-settings", response_model=DetectionSettingsRead)
async def read_detection_settings(
    camera_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.get_detection_settings(db, camera_id)


@router.put("/{camera_id}/detection-settings", response_model=DetectionSettingsRead)
async def write_detection_settings(
    camera_id: UUID,
    body: DetectionSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.update_detection_settings(db, camera_id, body)
