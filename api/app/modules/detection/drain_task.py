# app/modules/detection/drain_task.py
"""
Polls DetectionManager's alert queue and persists YOLO detection alerts as
Events — the same "capture on a thread, sync via queue" pattern as
app/modules/events/drain_task.py's motion_event_drain_loop, kept as a
separate loop/file so that file stays untouched.

Note this is deliberately a second, lightweight Event per alert (subtype
"yolo", no clip_path, confidence on YOLO's 0-1 scale) alongside whatever
recording clip Event the untouched motion/frame_diff pipeline in
recording_manager.py also produces from the same MotionResult (subtype
"frame_diff", with the actual clip_path) — recording_manager.py has no
concept of detector backend, so it always labels its own clip events as
"motion"/"frame_diff" regardless of whether motion-diff or YOLO produced
them. This "detection" event is the alert record (what triggered MQTT/CoT
publishing); the "frame_diff" event remains the recorded-clip metadata.
"""

import asyncio
import datetime as dt
import json
import logging
import uuid

from app.db.session import async_session_factory
from app.modules.events.model import Event
from app.services.storage import get_thumbnail_path

logger = logging.getLogger(__name__)


def _importance_for(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    if confidence >= 0.5:
        return "medium"
    return "low"


async def _persist_alerts(alerts: list[dict]) -> None:
    async with async_session_factory() as db:
        try:
            for alert in alerts:
                event_id = alert.get("alert_id") or str(uuid.uuid4())
                started_at = dt.datetime.fromtimestamp(
                    alert["timestamp"], tz=dt.timezone.utc
                )

                thumbnail_path = None
                snapshot = alert.get("snapshot_jpeg")
                if snapshot:
                    try:
                        path = get_thumbnail_path(event_id)
                        path.write_bytes(snapshot)
                        thumbnail_path = str(path)
                    except OSError as exc:
                        logger.warning(
                            "Failed writing detection thumbnail for %s: %s", event_id, exc
                        )

                confidence = float(alert.get("confidence", 0.0))
                metadata = {
                    "class_names": alert.get("class_names", []),
                    "detections": [
                        {
                            "class_name": d.get("class_name"),
                            "confidence": d.get("confidence"),
                            "bbox": list(d.get("bbox", [])),
                        }
                        for d in alert.get("detections", [])
                    ],
                }

                db.add(
                    Event(
                        id=uuid.UUID(event_id),
                        camera_id=alert["camera_id"],
                        event_type="detection",
                        subtype="yolo",
                        started_at=started_at,
                        ended_at=started_at,
                        confidence=confidence,
                        importance=_importance_for(confidence),
                        thumbnail_path=thumbnail_path,
                        clip_path=None,
                        clip_duration_seconds=None,
                        alerted=True,
                        metadata_json=json.dumps(metadata),
                    )
                )
            await db.commit()
            logger.info("Persisted %d detection alerts", len(alerts))
        except Exception as e:
            await db.rollback()
            logger.error("Failed to persist detection alerts: %s", e, exc_info=True)


async def detection_alert_drain_loop():
    """Polls DetectionManager's alert queue and persists detection events."""
    from app.modules.detection.manager import DetectionManager

    logger.info("Detection alert drain loop started")
    mgr = DetectionManager.get_instance()

    while True:
        try:
            alerts = mgr.drain_alerts()
            if alerts:
                await _persist_alerts(alerts)
        except Exception as e:
            logger.error("Detection drain loop error: %s", e, exc_info=True)

        await asyncio.sleep(2)
