from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Camera(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "cameras"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    location_label: Mapped[str] = mapped_column(String(200), default="")
    rtsp_url_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="offline")
    record_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    retention_days: Mapped[int] = mapped_column(Integer, default=14)

    zones: Mapped[list["CameraZone"]] = relationship(
        back_populates="camera", cascade="all, delete-orphan"
    )


class CameraZone(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "camera_zones"

    camera_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    polygon_json: Mapped[str] = mapped_column(Text, default="[]")
    zone_type: Mapped[str] = mapped_column(String(50), default="detection")

    camera: Mapped["Camera"] = relationship(back_populates="zones")