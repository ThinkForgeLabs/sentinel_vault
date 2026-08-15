import uuid
from datetime import datetime

from pydantic import BaseModel, Field

DEVICE_TYPES = (
    "presence_sensor",
    "door_sensor",
    "window_sensor",
    "doorbell_button",
    "other",
)
PROTOCOLS = ("esphome", "zigbee2mqtt")


class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    device_type: str = Field(..., min_length=1, max_length=50)
    location_label: str = ""
    protocol: str = Field(..., min_length=1, max_length=50)
    mqtt_topic: str = Field(..., min_length=1, max_length=500)
    enabled: bool = True


class DeviceUpdate(BaseModel):
    name: str | None = None
    device_type: str | None = None
    location_label: str | None = None
    protocol: str | None = None
    mqtt_topic: str | None = None
    enabled: bool | None = None
    status: str | None = None


class DeviceOut(BaseModel):
    id: uuid.UUID
    name: str
    device_type: str
    location_label: str
    protocol: str
    mqtt_topic: str
    status: str
    enabled: bool
    last_seen_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
