# app/modules/realtime/schemas.py

from pydantic import BaseModel, Field


class AlertSettingsRead(BaseModel):
    websocket_enabled: bool = True
    lan_broadcast_enabled: bool = True
    lan_broadcast_port: int = 37020
    min_importance: str = "low"


class AlertSettingsUpdate(BaseModel):
    websocket_enabled: bool | None = None
    lan_broadcast_enabled: bool | None = None
    lan_broadcast_port: int | None = Field(None, ge=1024, le=65535)
    min_importance: str | None = None


class ConnectionStatus(BaseModel):
    connected_clients: int


class AlertMessage(BaseModel):
    """Payload broadcast to every WebSocket client and the LAN UDP channel
    whenever a new event is persisted or a camera changes status."""

    type: str = "event"
    event_id: str | None = None
    camera_id: str
    camera_name: str | None = None
    event_type: str
    subtype: str | None = None
    importance: str = "low"
    confidence: float = 0.0
    started_at: str
    thumbnail_url: str | None = None
    clip_url: str | None = None
