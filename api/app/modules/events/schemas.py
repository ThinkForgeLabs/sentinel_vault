# app/modules/events/schemas.py

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator


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
    subtype: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    confidence: float
    importance: str
    thumbnail_path: str | None = None
    clip_path: str | None = None
    clip_duration_seconds: float | None = None
    alerted: bool
    review_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


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

    model_config = ConfigDict(from_attributes=True)


class EventResponse(BaseModel):
    id: uuid.UUID
    camera_id: uuid.UUID
    event_type: str
    subtype: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    confidence: float = 0
    importance: str = "low"
    thumbnail_path: str | None = None
    clip_path: str | None = None
    clip_duration_seconds: float | None = None
    has_clip: bool = False
    thumbnail_url: str | None = None
    clip_url: str | None = None
    review_status: str = "pending"
    metadata_json: str = "{}"

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def compute_urls(self):
        if self.clip_path:
            self.has_clip = True
            self.clip_url = f"/api/v1/events/{self.id}/clip"
        if self.thumbnail_path:
            self.thumbnail_url = f"/api/v1/events/{self.id}/thumbnail"
        return self