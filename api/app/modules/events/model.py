from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Detection(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "detections"

    camera_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    track_id: Mapped[str | None] = mapped_column(String(100), index=True)
    detection_type: Mapped[str] = mapped_column(String(50), nullable=False)
    bbox_json: Mapped[str] = mapped_column(Text, default="[]")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    frame_ref: Mapped[str | None] = mapped_column(String(500))


class Event(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "events"

    camera_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False
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