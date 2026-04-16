# app/modules/detection/service.py

import json
import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.service import upsert_setting, get_setting
from .schemas import MotionSettingsRead, MotionSettingsUpdate
from .manager import DetectionManager

logger = logging.getLogger(__name__)

DEFAULTS = {
    "enabled": True,
    "threshold": 25,
    "min_contour_area": 500,
}


def _key(camera_id: UUID) -> str:
    return f"motion_settings_{camera_id}"


async def get_motion_settings(
    db: AsyncSession, camera_id: UUID
) -> MotionSettingsRead:
    raw = await get_setting(db, _key(camera_id))
    if raw:
        data = json.loads(raw)
        data.pop("cooldown_seconds", None)  # strip legacy key
    else:
        data = DEFAULTS.copy()
    return MotionSettingsRead(camera_id=camera_id, **data)


async def update_motion_settings(
    db: AsyncSession, camera_id: UUID, update: MotionSettingsUpdate
) -> MotionSettingsRead:
    current = await get_motion_settings(db, camera_id)
    merged = current.model_dump(exclude={"camera_id"})

    for field_name, value in update.model_dump(exclude_unset=True).items():
        merged[field_name] = value

    await upsert_setting(db, _key(camera_id), json.dumps(merged))

    DetectionManager.get_instance().update_config(str(camera_id), **merged)

    return MotionSettingsRead(camera_id=camera_id, **merged)


async def init_detectors(db: AsyncSession, camera_ids: list[str]):
    """Called at startup — loads saved settings and registers detectors."""
    mgr = DetectionManager.get_instance()
    for cid in camera_ids:
        settings = await get_motion_settings(db, UUID(cid))
        mgr.register(
            cid,
            enabled=settings.enabled,
            threshold=settings.threshold,
            min_contour_area=settings.min_contour_area,
        )
    logger.info("Initialized %d motion detectors", len(camera_ids))