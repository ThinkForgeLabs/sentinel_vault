import uuid
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.events.model import Event
from app.modules.playback.schemas import (
    AvailabilityResponse,
    AvailabilitySegment,
    BatchAvailabilityRequest,
    BatchAvailabilityResponse,
    StreamInfo,
    TimelineEvent,
)
from app.modules.recordings.model import Recording


async def get_availability(
    db: AsyncSession,
    camera_id: uuid.UUID,
    start: datetime,
    end: datetime,
) -> AvailabilityResponse:
    result = await db.execute(
        select(Recording)
        .where(
            and_(
                Recording.camera_id == camera_id,
                Recording.status == "complete",
                Recording.start_time < end,
                Recording.end_time > start,
            )
        )
        .order_by(Recording.start_time)
    )
    recordings = result.scalars().all()

    segments = [
        AvailabilitySegment(
            start=rec.start_time,
            end=rec.end_time,
            recording_id=str(rec.id),
            duration_seconds=rec.duration_seconds or 0.0,
        )
        for rec in recordings
    ]

    return AvailabilityResponse(camera_id=camera_id, segments=segments)


async def get_stream_info(camera_id: uuid.UUID) -> StreamInfo:
    return StreamInfo(
        camera_id=camera_id,
        stream_url=f"/api/v1/playback/stream/{camera_id}/live.m3u8",
        codec="H.264",
        resolution="1920x1080",
    )


async def get_batch_availability(
    db: AsyncSession, request: BatchAvailabilityRequest
) -> BatchAvailabilityResponse:
    """Same query as get_availability, run once per camera — lets the
    multicamera wall view load every tile's segments in a single request
    instead of N round trips."""
    cameras: dict[str, list[AvailabilitySegment]] = {}
    for camera_id in request.camera_ids:
        availability = await get_availability(db, camera_id, request.start, request.end)
        cameras[str(camera_id)] = availability.segments
    return BatchAvailabilityResponse(cameras=cameras)


async def get_timeline_events(
    db: AsyncSession,
    camera_ids: list[uuid.UUID],
    start: datetime,
    end: datetime,
) -> list[TimelineEvent]:
    """Event markers to overlay on the Frigate-style timeline, across one
    or more cameras, within a time range."""
    result = await db.execute(
        select(Event)
        .where(
            and_(
                Event.camera_id.in_(camera_ids),
                Event.started_at < end,
                Event.started_at >= start,
            )
        )
        .order_by(Event.started_at)
    )
    events = result.scalars().all()
    return [
        TimelineEvent(
            event_id=ev.id,
            camera_id=ev.camera_id,
            started_at=ev.started_at,
            ended_at=ev.ended_at,
            event_type=ev.event_type,
            importance=ev.importance,
        )
        for ev in events
    ]