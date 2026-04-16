from pathlib import Path
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

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

@router.get("/{event_id}/clip")
async def get_event_clip(event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or not event.clip_path:
        raise HTTPException(404, "No clip for this event")
    clip = Path(event.clip_path)
    if not clip.exists():
        raise HTTPException(404, "Clip file missing from disk")
    return FileResponse(clip, media_type="video/mp4", filename=clip.name)


@router.get("/{event_id}/thumbnail")
async def get_event_thumbnail(event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event or not event.thumbnail_path:
        raise HTTPException(404, "No thumbnail for this event")
    thumb = Path(event.thumbnail_path)
    if not thumb.exists():
        raise HTTPException(404, "Thumbnail file missing from disk")
    return FileResponse(thumb, media_type="image/jpeg")