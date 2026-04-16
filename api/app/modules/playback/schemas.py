import uuid
from datetime import datetime

from pydantic import BaseModel


class AvailabilitySegment(BaseModel):
    start: datetime
    end: datetime
    recording_id: str | None = None
    duration_seconds: float = 0.0

    model_config = {"from_attributes": True}


class AvailabilityResponse(BaseModel):
    camera_id: uuid.UUID
    segments: list[AvailabilitySegment]


class StreamInfo(BaseModel):
    camera_id: uuid.UUID
    stream_url: str
    codec: str
    resolution: str