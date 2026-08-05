import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RecordingOut(BaseModel):
    id: uuid.UUID
    camera_id: uuid.UUID
    start_time: datetime
    end_time: datetime
    file_size: int
    duration_seconds: float
    resolution: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class RecordingFilters(BaseModel):
    camera_id: uuid.UUID | None = None
    status: str | None = None
    after: datetime | None = None
    before: datetime | None = None


# ── Storage ──


class CameraBreakdown(BaseModel):
    camera_id: str
    camera_name: str
    retention_days: int
    recording_count: int
    size_bytes: int


class StorageStats(BaseModel):
    disk_total_bytes: int
    disk_used_bytes: int
    disk_free_bytes: int
    disk_usage_percent: float
    recordings_total_bytes: int
    recordings_count: int
    recordings_total_duration_seconds: float
    max_storage_gb: float | None
    storage_warning_percent: int
    storage_warning_active: bool
    per_camera: list[CameraBreakdown]


class StorageSettingsPayload(BaseModel):
    max_storage_gb: float | None = None
    storage_warning_percent: int = Field(default=90, ge=50, le=99)


class CleanupResult(BaseModel):
    expired_deleted: int
    cap_deleted: int
    orphans_removed: int
    empty_dirs_removed: int
