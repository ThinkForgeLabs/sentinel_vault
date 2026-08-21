# app/services/notifications.py
"""
Notification dispatcher — sends real-time alerts through every enabled
channel: an in-app WebSocket broadcast (app.modules.realtime.manager) and a
LAN UDP broadcast (app.services.lan_broadcast). Channel toggles and the
minimum importance threshold are stored via the generic SystemSetting KV
store (see app.modules.realtime.service).
"""

from app.core.logging import get_logger
from app.modules.realtime.manager import connection_manager
from app.modules.realtime.schemas import AlertMessage, AlertSettingsRead
from app.modules.realtime.service import get_alert_settings
from app.services.lan_broadcast import send_broadcast_async

logger = get_logger("notifications")

IMPORTANCE_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


async def dispatch_event_alert(db, alert: AlertMessage) -> None:
    """Fan a persisted event out to every enabled alert channel.

    Never raises — a notification failure must never block event
    persistence or the async drain loops that call this.
    """
    try:
        settings = await get_alert_settings(db)
    except Exception as exc:
        logger.warning("Could not load alert settings, using defaults: %s", exc)
        settings = AlertSettingsRead()

    if IMPORTANCE_RANK.get(alert.importance, 0) < IMPORTANCE_RANK.get(
        settings.min_importance, 0
    ):
        return

    payload = alert.model_dump()

    if settings.websocket_enabled:
        try:
            await connection_manager.broadcast(payload)
        except Exception as exc:
            logger.warning("WebSocket broadcast failed: %s", exc)

    if settings.lan_broadcast_enabled:
        try:
            await send_broadcast_async(payload, port=settings.lan_broadcast_port)
        except Exception as exc:
            logger.warning("LAN broadcast failed: %s", exc)


async def send_desktop_notification(
    title: str,
    body: str,
    event_id: str | None = None,
) -> bool:
    """Lightweight WebSocket-only ping for callers that don't have a DB
    session handy (e.g. one-off admin actions)."""
    try:
        await connection_manager.broadcast(
            {"type": "notice", "title": title, "body": body, "event_id": event_id}
        )
        return True
    except Exception as exc:
        logger.warning("Desktop notification failed: %s", exc)
        return False
