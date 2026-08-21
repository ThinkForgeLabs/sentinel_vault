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


class BatchAvailabilityRequest(BaseModel):
    """Fetch availability for several cameras in one round trip — the
    wall-view timeline needs every camera's segments to stay in sync
    without firing one request per tile."""

    camera_ids: list[uuid.UUID]
    start: datetime
    end: datetime


class BatchAvailabilityResponse(BaseModel):
    cameras: dict[str, list[AvailabilitySegment]]


class TimelineEvent(BaseModel):
    """A single marker overlaid on the Frigate-style timeline."""

    event_id: uuid.UUID
    camera_id: uuid.UUID
    started_at: datetime
    ended_at: datetime | None = None
    event_type: str
    importance: str

    model_config = {"from_attributes": True}


class TimelineEventsResponse(BaseModel):
    events: list[TimelineEvent]