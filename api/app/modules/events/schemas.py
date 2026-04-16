import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EventFilters(BaseModel):
    camera_id: uuid.UUID | None = None
    event_type: str | None = None
    importance: str | None = None
    after: datetime | None = None
    before: datetime | None = None


class EventOut(BaseModel):
    id: uuid.UUID
    camera_id: uuid.UUID
    event_type: str
    subtype: str | None
    started_at: datetime
    ended_at: datetime | None
    confidence: float
    importance: str
    thumbnail_path: str | None
    clip_path: str | None
    clip_duration_seconds: int | None
    alerted: bool
    review_status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class EventUpdate(BaseModel):
    review_status: str | None = None
    importance: str | None = None


class EventStats(BaseModel):
    total_today: int
    by_type: dict[str, int]
    alerted_count: int


class DetectionOut(BaseModel):
    id: uuid.UUID
    camera_id: uuid.UUID
    timestamp: datetime
    detection_type: str
    score: float

    model_config = {"from_attributes": True}