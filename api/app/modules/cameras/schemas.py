import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CameraCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    location_label: str = ""
    rtsp_url: str = Field(..., min_length=1)
    record_enabled: bool = True
    ai_enabled: bool = False
    retention_days: int = Field(default=14, ge=1, le=365)


class CameraUpdate(BaseModel):
    name: str | None = None
    location_label: str | None = None
    rtsp_url: str | None = None
    record_enabled: bool | None = None
    ai_enabled: bool | None = None
    retention_days: int | None = None
    status: str | None = None


class CameraOut(BaseModel):
    id: uuid.UUID
    name: str
    location_label: str
    status: str
    record_enabled: bool
    ai_enabled: bool
    retention_days: int
    created_at: datetime

    model_config = {"from_attributes": True}


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