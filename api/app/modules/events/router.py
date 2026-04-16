from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.common import PaginationParams
from app.modules.auth.model import User
from app.modules.events.schemas import EventFilters, EventOut, EventStats, EventUpdate
from app.modules.events.service import get_event, get_event_stats, list_events, update_event

router = APIRouter()


@router.get("", response_model=list[EventOut])
async def get_events(
    camera_id: str | None = Query(None),
    event_type: str | None = Query(None),
    importance: str | None = Query(None),
    pagination: PaginationParams = Depends(),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    filters = EventFilters(camera_id=camera_id, event_type=event_type, importance=importance)
    return await list_events(db, filters, pagination.offset, pagination.limit)


@router.get("/stats", response_model=EventStats)
async def event_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await get_event_stats(db)


@router.get("/{event_id}", response_model=EventOut)
async def get_event_detail(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await get_event(db, event_id)


@router.patch("/{event_id}", response_model=EventOut)
async def patch_event(
    event_id: str,
    body: EventUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await update_event(db, event_id, body)