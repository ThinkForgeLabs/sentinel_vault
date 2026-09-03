from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
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
    retention_days: Mapped[int] = mapped_column(Integer, default=14)

    # ── detection (YOLO backend, ported from ODDS v3) ──
    detect_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    detect_backend: Mapped[str] = mapped_column(String(20), default="motion")  # "motion" | "yolo"
    model_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ml_models.id", ondelete="SET NULL"), nullable=True
    )
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.5)
    detect_class_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    alert_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    alert_cooldown_seconds: Mapped[int] = mapped_column(Integer, default=30)
    mqtt_publish_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    cot_publish_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    # Static surveyed position for CoT plotting only (no range/bearing math).
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)

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
