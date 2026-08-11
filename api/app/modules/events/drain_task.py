# app/modules/events/drain_task.py

import asyncio
import json
import logging

from app.db.session import async_session_factory
from app.modules.cameras.model import Camera
from app.modules.events.model import Event
from app.modules.realtime.schemas import AlertMessage
from app.modules.recordings.recording_manager import recording_manager
from app.services.notifications import dispatch_event_alert

logger = logging.getLogger(__name__)


async def _alert_for_event(db, event: Event) -> None:
    """Marks the event alerted and fans it out to every real-time alert
    channel. Isolated in its own try/except so a broadcast failure never
    prevents the next event in the batch from being processed."""
    try:
        camera = await db.get(Camera, event.camera_id)
        alert = AlertMessage(
            event_id=str(event.id),
            camera_id=str(event.camera_id),
            camera_name=camera.name if camera else None,
            event_type=event.event_type,
            subtype=event.subtype,
            importance=event.importance,
            confidence=event.confidence,
            started_at=event.started_at.isoformat(),
            thumbnail_url=f"/api/v1/events/{event.id}/thumbnail" if event.thumbnail_path else None,
            clip_url=f"/api/v1/events/{event.id}/clip" if event.clip_path else None,
        )
        await dispatch_event_alert(db, alert)
        event.alerted = True
        await db.commit()
    except Exception as exc:
        logger.warning("Failed to dispatch alert for event %s: %s", event.id, exc)


async def motion_event_drain_loop():
    """Polls the recording manager queue and persists motion events."""
    logger.info("Motion event drain loop started")

    while True:
        try:
            events = recording_manager.drain_motion_events()
            if events:
                async with async_session_factory() as db:
                    try:
                        persisted: list[Event] = []
                        for ev in events:
                            event = Event(
                                id=ev["id"],
                                camera_id=ev["camera_id"],
                                event_type=ev.get("event_type", "motion"),
                                subtype=ev.get("subtype", "frame_diff"),
                                started_at=ev["started_at"],
                                ended_at=ev.get("ended_at"),
                                confidence=ev.get("confidence", 0),
                                importance=ev.get("importance", "low"),
                                thumbnail_path=ev.get("thumbnail_path"),
                                clip_path=ev.get("clip_path"),
                                clip_duration_seconds=(
                                    round(ev["clip_duration_seconds"])
                                    if ev.get("clip_duration_seconds") is not None
                                    else None
                                ),
                                metadata_json=json.dumps(ev.get("metadata", {})),
                            )
                            db.add(event)
                            persisted.append(event)
                        await db.commit()
                        logger.info("Persisted %d motion events", len(events))

                        # ── Real-time alert fan-out ──
                        # Runs after commit so a slow/failed alert channel
                        # never rolls back an already-persisted event.
                        for event in persisted:
                            await _alert_for_event(db, event)
                    except Exception as e:
                        await db.rollback()
                        logger.error("Failed to persist motion events: %s", e, exc_info=True)
        except Exception as e:
            logger.error("Drain loop error: %s", e, exc_info=True)

        await asyncio.sleep(2)