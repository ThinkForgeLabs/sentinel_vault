import uuid
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.playback.schemas import (
    AvailabilityResponse,
    AvailabilitySegment,
    StreamInfo,
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