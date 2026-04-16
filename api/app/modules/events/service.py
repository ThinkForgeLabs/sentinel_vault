from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.events.model import Event
from app.modules.events.schemas import EventFilters, EventStats, EventUpdate


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