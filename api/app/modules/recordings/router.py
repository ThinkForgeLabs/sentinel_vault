import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.modules.auth.model import User
from app.modules.recordings import service
from app.modules.recordings.schemas import (
    CleanupResult,
    RecordingFilters,
    RecordingOut,
    StorageSettingsPayload,
    StorageStats,
)
from app.services.video_crypto import cleanup_task, decrypt_to_temp

router = APIRouter()


# ── Storage — declared before /{recording_id} so "storage" isn't
#    swallowed by the recording-id path parameter ──


@router.get("/storage", response_model=StorageStats)
async def storage_stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await service.get_storage_stats(db)


@router.get("/storage/settings", response_model=StorageSettingsPayload)
async def read_storage_settings(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await service.get_storage_settings(db)


@router.put("/storage/settings", response_model=StorageSettingsPayload)
async def write_storage_settings(
    body: StorageSettingsPayload,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await service.update_storage_settings(db, body)


@router.post("/storage/cleanup", response_model=CleanupResult)
async def storage_cleanup(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await service.run_cleanup(db)


# ── Recordings list / detail / download / delete ──


@router.get("", response_model=list[RecordingOut])
async def get_recordings(
    camera_id: uuid.UUID | None = Query(None),
    status: str | None = Query(None),
    after: datetime | None = Query(None),
    before: datetime | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    filters = RecordingFilters(camera_id=camera_id, status=status, after=after, before=before)
    return await service.list_recordings(db, filters, offset=offset, limit=limit)


@router.get("/{recording_id}", response_model=RecordingOut)
async def get_recording_detail(
    recording_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await service.get_recording(db, recording_id)


@router.get("/{recording_id}/download")
async def download_recording(
    recording_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    recording = await service.get_recording(db, recording_id)
    path = Path(recording.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Recording file missing from disk")

    # Recordings are encrypted at rest — decrypt into a short-lived temp
    # file for this download, then delete it once the response is sent.
    temp_path = decrypt_to_temp(path, suffix=path.suffix)

    return FileResponse(
        temp_path,
        media_type="video/x-msvideo",
        filename=f"{recording.camera_id}_{recording.start_time.isoformat()}{path.suffix}",
        background=cleanup_task(temp_path),
    )


@router.delete("/{recording_id}", status_code=204)
async def remove_recording(
    recording_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    await service.delete_recording(db, recording_id)
