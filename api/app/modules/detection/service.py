# app/modules/detection/service.py

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.cameras.model import Camera
from app.modules.ml_models.service import get_default_model, get_model
from app.modules.settings.schemas import SettingUpdate
from app.modules.settings.service import get_setting, upsert_setting

from .manager import DetectionManager
from .schemas import (
    DetectionEngineStatus,
    DetectionSettingsRead,
    DetectionSettingsUpdate,
    MotionSettingsRead,
    MotionSettingsUpdate,
)

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
        data = json.loads(raw.value_json)
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

    await upsert_setting(db, _key(camera_id), SettingUpdate(value_json=json.dumps(merged)))

    DetectionManager.get_instance().update_config(str(camera_id), **merged)

    return MotionSettingsRead(camera_id=camera_id, **merged)


async def init_detectors(db: AsyncSession, camera_ids: list[str]):
    """Called at startup — loads saved settings and registers detectors.

    Motion-backend cameras keep the original path (settings pulled from the
    generic settings-table JSON blob). Cameras configured for the YOLO
    backend instead read their detection config straight off the Camera row
    (see DetectionSettingsRead/Update) and register a YoloDetector.
    """
    mgr = DetectionManager.get_instance()
    for cid in camera_ids:
        camera = await db.get(Camera, UUID(cid))
        if camera is not None and camera.detect_backend == "yolo":
            await _register_yolo(db, camera, mgr)
            continue

        settings = await get_motion_settings(db, UUID(cid))
        mgr.register(
            cid,
            backend="motion",
            enabled=settings.enabled,
            threshold=settings.threshold,
            min_contour_area=settings.min_contour_area,
        )
    logger.info("Initialized %d detectors", len(camera_ids))


def _class_ids_from_camera(camera: Camera) -> list[int]:
    try:
        return json.loads(camera.detect_class_ids_json)
    except (json.JSONDecodeError, TypeError):
        return []


async def _register_yolo(db: AsyncSession, camera: Camera, mgr: DetectionManager) -> None:
    model_path = None
    if camera.model_id is not None:
        try:
            model = await get_model(db, camera.model_id)
            model_path = model.file_path
        except NotFoundError:
            logger.warning(
                "Camera %s references missing model %s — falling back to default",
                camera.id, camera.model_id,
            )
    if model_path is None:
        default_model = await get_default_model(db)
        model_path = default_model.file_path if default_model else None

    mgr.sync_camera(
        str(camera.id),
        backend="yolo",
        enabled=camera.detect_enabled,
        model_path=model_path,
        confidence=camera.confidence_threshold,
        class_ids=_class_ids_from_camera(camera),
        alert_enabled=camera.alert_enabled,
        alert_cooldown=camera.alert_cooldown_seconds,
        camera_name=camera.name,
        location_label=camera.location_label,
        latitude=camera.latitude,
        longitude=camera.longitude,
        mqtt_publish_enabled=camera.mqtt_publish_enabled,
        cot_publish_enabled=camera.cot_publish_enabled,
    )


async def get_detection_settings(db: AsyncSession, camera_id: UUID) -> DetectionSettingsRead:
    camera = await db.get(Camera, camera_id)
    if camera is None:
        raise NotFoundError("Camera", camera_id)
    return DetectionSettingsRead(
        camera_id=camera.id,
        detect_enabled=camera.detect_enabled,
        detect_backend=camera.detect_backend,
        model_id=camera.model_id,
        confidence_threshold=camera.confidence_threshold,
        detect_class_ids=_class_ids_from_camera(camera),
        alert_enabled=camera.alert_enabled,
        alert_cooldown_seconds=camera.alert_cooldown_seconds,
        mqtt_publish_enabled=camera.mqtt_publish_enabled,
        cot_publish_enabled=camera.cot_publish_enabled,
    )


async def update_detection_settings(
    db: AsyncSession, camera_id: UUID, update: DetectionSettingsUpdate
) -> DetectionSettingsRead:
    camera = await db.get(Camera, camera_id)
    if camera is None:
        raise NotFoundError("Camera", camera_id)

    changes = update.model_dump(exclude_unset=True)
    if "detect_class_ids" in changes:
        camera.detect_class_ids_json = json.dumps(changes.pop("detect_class_ids"))
    for field_name, value in changes.items():
        setattr(camera, field_name, value)

    await db.flush()
    await sync_camera_to_detector(db, camera)

    return await get_detection_settings(db, camera_id)


async def sync_camera_to_detector(db: AsyncSession, camera: Camera) -> None:
    """Re-registers this camera's detector to match its current DB row —
    call after any change to detect_backend/model_id/thresholds/etc."""
    mgr = DetectionManager.get_instance()
    if camera.detect_backend == "yolo":
        await _register_yolo(db, camera, mgr)
    else:
        mgr.sync_camera(
            str(camera.id),
            backend="motion",
            enabled=camera.detect_enabled,
        )


async def get_engine_status(db: AsyncSession) -> list[DetectionEngineStatus]:
    mgr = DetectionManager.get_instance()
    result = await db.execute(select(Camera.id))
    camera_ids = [row[0] for row in result.all()]

    statuses = []
    for cid in camera_ids:
        detector = mgr.get_detector(str(cid))
        backend = mgr.get_backend(str(cid)) or "none"
        last_trigger = None
        if detector is not None and detector.last_trigger_time > 0:
            last_trigger = datetime.fromtimestamp(detector.last_trigger_time, tz=timezone.utc)
        statuses.append(
            DetectionEngineStatus(
                camera_id=cid,
                backend=backend,
                detector_active=detector is not None,
                model_path=getattr(detector, "model_path", None),
                frames_processed=getattr(detector, "frames_processed", 0),
                detections=getattr(detector, "detection_count", 0),
                last_trigger=last_trigger,
            )
        )
    return statuses
