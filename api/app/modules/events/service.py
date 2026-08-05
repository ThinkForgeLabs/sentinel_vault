from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.events.model import Event
from app.modules.events.schemas import EventFilters, EventStats, EventUpdate

import json
from uuid import uuid4

async def list_events(
    db: AsyncSession,
    filters: EventFilters,
    offset: int = 0,
    limit: int = 20,
) -> list[Event]:
    stmt = select(Event).order_by(Event.started_at.desc())

    if filters.camera_id:
        stmt = stmt.where(Event.camera_id == filters.camera_id)
    if filters.event_type:
        stmt = stmt.where(Event.event_type == filters.event_type)
    if filters.importance:
        stmt = stmt.where(Event.importance == filters.importance)
    if filters.after:
        stmt = stmt.where(Event.started_at >= filters.after)
    if filters.before:
        stmt = stmt.where(Event.started_at <= filters.before)

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_event(db: AsyncSession, event_id: str) -> Event:
    event = await db.get(Event, event_id)
    if event is None:
        raise NotFoundError("Event", event_id)
    return event


async def update_event(db: AsyncSession, event_id: str, data: EventUpdate) -> Event:
    event = await get_event(db, event_id)
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(event, key, value)
    await db.flush()
    return event


async def get_event_stats(db: AsyncSession) -> EventStats:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    # Total today
    total_result = await db.execute(
        select(func.count(Event.id)).where(Event.started_at >= today_start)
    )
    total = total_result.scalar() or 0

    # By type
    type_result = await db.execute(
        select(Event.event_type, func.count(Event.id))
        .where(Event.started_at >= today_start)
        .group_by(Event.event_type)
    )
    by_type = dict(type_result.all())

    # Alerted
    alerted_result = await db.execute(
        select(func.count(Event.id)).where(
            Event.started_at >= today_start, Event.alerted.is_(True)
        )
    )
    alerted = alerted_result.scalar() or 0

    return EventStats(total_today=total, by_type=by_type, alerted_count=alerted)
async def create_motion_event(db: AsyncSession, event_data: dict) -> Event:
    """Create an Event row from a motion detection result."""
    event = Event(
        id=event_data.get("id", uuid4()),
        camera_id=event_data["camera_id"],
        event_type="motion",
        subtype=event_data.get("subtype", "frame_diff"),
        started_at=event_data["started_at"],
        ended_at=event_data.get("ended_at"),
        confidence=event_data.get("confidence", 0.0),
        importance=event_data.get("importance", "low"),
        thumbnail_path=event_data.get("thumbnail_path"),
        clip_path=event_data.get("clip_path"),
        clip_duration_seconds=(
            round(event_data["clip_duration_seconds"])
            if event_data.get("clip_duration_seconds") is not None
            else None
        ),
        alerted=False,
        review_status="pending",
        metadata_json=json.dumps(event_data.get("metadata", {})),
    )
    db.add(event)
    await db.flush()
    return event