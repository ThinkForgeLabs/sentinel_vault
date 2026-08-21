from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, UUIDMixin


class Event(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "events"

    # Exactly one of camera_id / device_id is set, enforced at the service
    # layer (create_motion_event / camera_status_sync_loop always set
    # camera_id; the MQTT ingest task always sets device_id). Both are
    # nullable so the same Event table can carry video-camera events and
    # non-camera sensor events (door/presence/doorbell) side by side.
    camera_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=True
    )
    device_id: Mapped[str | None] = mapped_column(
        GUID(), ForeignKey("devices.id", ondelete="CASCADE"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    subtype: Mapped[str | None] = mapped_column(String(100))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    importance: Mapped[str] = mapped_column(String(20), default="medium")
    thumbnail_path: Mapped[str | None] = mapped_column(String(500))
    clip_path: Mapped[str | None] = mapped_column(String(500))
    clip_duration_seconds: Mapped[int | None] = mapped_column(Integer)
    alerted: Mapped[bool] = mapped_column(Boolean, default=False)
    review_status: Mapped[str] = mapped_column(String(50), default="pending")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")