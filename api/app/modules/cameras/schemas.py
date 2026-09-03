import json
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CameraCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    location_label: str = ""
    rtsp_url: str = Field(..., min_length=1)
    record_enabled: bool = True
    retention_days: int = Field(default=14, ge=1, le=365)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class CameraUpdate(BaseModel):
    name: str | None = None
    location_label: str | None = None
    rtsp_url: str | None = None
    record_enabled: bool | None = None
    retention_days: int | None = None
    status: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class CameraOut(BaseModel):
    id: uuid.UUID
    name: str
    location_label: str
    status: str
    record_enabled: bool
    retention_days: int
    created_at: datetime

    detect_enabled: bool = False
    detect_backend: str = "motion"
    model_id: uuid.UUID | None = None
    confidence_threshold: float = 0.5
    detect_class_ids_json: str = "[]"
    detect_class_ids: list[int] = []
    alert_enabled: bool = True
    alert_cooldown_seconds: int = 30
    mqtt_publish_enabled: bool = False
    cot_publish_enabled: bool = False
    latitude: float | None = None
    longitude: float | None = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def parse_class_ids(self):
        try:
            self.detect_class_ids = json.loads(self.detect_class_ids_json)
        except (json.JSONDecodeError, TypeError):
            self.detect_class_ids = []
        return self


class CameraDetail(CameraOut):
    zones: list["ZoneOut"] = []


class ZoneOut(BaseModel):
    id: uuid.UUID
    name: str
    polygon_json: str
    zone_type: str

    model_config = {"from_attributes": True}


class TestConnectionRequest(BaseModel):
    rtsp_url: str


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    codec: str | None = None
    resolution: str | None = None


class DiscoveredDevice(BaseModel):
    index: int
    name: str
    resolution: str
    working: bool
    url: str
