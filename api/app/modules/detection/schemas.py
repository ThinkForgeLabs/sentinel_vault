from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MotionSettingsRead(BaseModel):
    camera_id: UUID
    enabled: bool = True
    threshold: int = 25
    min_contour_area: int = 500
    cooldown_seconds: float = 30.0

    model_config = {"from_attributes": True}


class MotionSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    threshold: Optional[int] = Field(None, ge=1, le=100)
    min_contour_area: Optional[int] = Field(None, ge=100, le=50000)
    cooldown_seconds: Optional[float] = Field(None, ge=5.0, le=300.0)


class MotionStatusRead(BaseModel):
    camera_id: UUID
    detector_active: bool
    enabled: bool
    frames_processed: int
    last_trigger: Optional[datetime] = None


class DetectionSettingsRead(BaseModel):
    camera_id: UUID
    detect_enabled: bool = False
    detect_backend: str = "motion"
    model_id: Optional[UUID] = None
    confidence_threshold: float = 0.5
    detect_class_ids: list[int] = Field(default_factory=list)
    alert_enabled: bool = True
    alert_cooldown_seconds: int = 30
    mqtt_publish_enabled: bool = False
    cot_publish_enabled: bool = False

    model_config = {"from_attributes": True}


class DetectionSettingsUpdate(BaseModel):
    detect_enabled: Optional[bool] = None
    detect_backend: Optional[str] = Field(None, pattern="^(motion|yolo)$")
    model_id: Optional[UUID] = None
    confidence_threshold: Optional[float] = Field(None, ge=0.05, le=1.0)
    detect_class_ids: Optional[list[int]] = None
    alert_enabled: Optional[bool] = None
    alert_cooldown_seconds: Optional[int] = Field(None, ge=0, le=3600)
    mqtt_publish_enabled: Optional[bool] = None
    cot_publish_enabled: Optional[bool] = None


class DetectionEngineStatus(BaseModel):
    camera_id: UUID
    backend: str
    detector_active: bool
    model_path: Optional[str] = None
    frames_processed: int = 0
    detections: int = 0
    last_trigger: Optional[datetime] = None
