from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import GUID, Base, TimestampMixin, UUIDMixin


class Recording(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "recordings"

    camera_id: Mapped[str] = mapped_column(
        GUID(), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False, index=True
    )
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0.0)
    resolution: Mapped[str] = mapped_column(String(50), default="")
    # "recording" (segment actively being written) | "complete" | "failed"
    status: Mapped[str] = mapped_column(String(50), default="recording", index=True)
