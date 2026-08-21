from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class Device(UUIDMixin, TimestampMixin, Base):
    """A non-camera sensor/actuator ingested over MQTT (ESPHome or
    Zigbee2MQTT) — presence sensors, door/window sensors, doorbell
    buttons, etc. Cameras stay in the Camera model; devices are for
    everything else that feeds the Events pipeline.
    """

    __tablename__ = "devices"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # "presence_sensor" | "door_sensor" | "window_sensor" | "doorbell_button" | "other"
    device_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    location_label: Mapped[str] = mapped_column(String(200), default="")
    # "esphome" | "zigbee2mqtt" — which stack publishes this device's state.
    protocol: Mapped[str] = mapped_column(String(50), nullable=False)
    # Exact MQTT state topic to match incoming messages against, e.g.
    # "esphome/front-door-presence/presence" or
    # "zigbee2mqtt/Back Door Sensor".
    mqtt_topic: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="offline")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
