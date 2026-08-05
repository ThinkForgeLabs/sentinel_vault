# app/modules/events/drain_task.py

import asyncio
import json
import logging

from app.db.session import async_session_factory
from app.modules.events.model import Event
from app.modules.recordings.recording_manager import recording_manager

logger = logging.getLogger(__name__)


async def motion_event_drain_loop():
    """Polls the recording manager queue and persists motion events."""
    logger.info("Motion event drain loop started")

    while True:
        try:
            events = recording_manager.drain_motion_events()
            if events:
                async with async_session_factory() as db:
                    try:
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
                        await db.commit()
                        logger.info("Persisted %d motion events", len(events))
                    except Exception as e:
                        await db.rollback()
                        logger.error("Failed to persist motion events: %s", e, exc_info=True)
        except Exception as e:
            logger.error("Drain loop error: %s", e, exc_info=True)

        await asyncio.sleep(2)