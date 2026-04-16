from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


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