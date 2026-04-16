"""
Notification dispatcher — sends alerts through configured channels.
v1 supports desktop (WebSocket) and log-based notifications.
"""

from app.core.logging import get_logger

logger = get_logger("notifications")


async def send_desktop_notification(
    title: str,
    body: str,
    event_id: str | None = None,
) -> bool:
    # In production, this pushes via WebSocket to connected clients
    logger.info("[desktop] %s: %s (event=%s)", title, body, event_id)
    return True


async def send_push_notification(
    user_id: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> bool:
    # Placeholder — requires push gateway configuration
    logger.info("[push] → user %s: %s", user_id, title)
    return True


async def dispatch_alert(
    channel: str,
    title: str,
    body: str,
    event_id: str | None = None,
    user_id: str | None = None,
) -> bool:
    if channel == "desktop":
        return await send_desktop_notification(title, body, event_id)
    elif channel == "push":
        return await send_push_notification(user_id or "", title, body, {"event_id": event_id})
    else:
        logger.warning("Unknown notification channel: %s", channel)
        return False