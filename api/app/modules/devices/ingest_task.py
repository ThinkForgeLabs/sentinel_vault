"""
Bridges the threaded MqttManager with the database — the sensor
equivalent of app/modules/events/drain_task.py's motion_event_drain_loop
and app/modules/recordings/tasks.py's camera_status_sync_loop. Started
from main.py's lifespan only when settings.mqtt_enabled is True.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import async_session_factory
from app.modules.devices.model import Device
from app.modules.devices.mqtt_manager import mqtt_manager
from app.modules.devices.sensor_parser import (
    device_matches_status_topic,
    event_type_for_state,
    extract_binary_state,
    importance_for_event_type,
    is_status_topic,
    parse_status_payload,
    status_topic_base,
)
from app.modules.events.model import Event
from app.modules.realtime.schemas import AlertMessage
from app.services.notifications import dispatch_event_alert

logger = logging.getLogger(__name__)

INGEST_INTERVAL_SECONDS = 2


async def _load_enabled_devices(db) -> list[Device]:
    result = await db.execute(select(Device).where(Device.enabled.is_(True)))
    return list(result.scalars().all())


def _match_device(message: dict, devices: list[Device]) -> Device | None:
    topic = message["topic"]
    if is_status_topic(topic):
        base = status_topic_base(topic)
        for device in devices:
            if device_matches_status_topic(device.mqtt_topic, base):
                return device
        return None

    for device in devices:
        if device.mqtt_topic == topic:
            return device
    return None


async def _handle_status_message(db, device: Device, payload: str, alerts: list) -> None:
    new_status = parse_status_payload(payload)
    if new_status is None or new_status == device.status:
        return

    now = datetime.now(timezone.utc)
    previous_status = device.status
    device.status = new_status
    device.last_seen_at = now

    if new_status == "offline" and previous_status != "offline":
        offline_event = Event(
            id=uuid.uuid4(),
            device_id=device.id,
            event_type="device_offline",
            started_at=now,
            importance="high",
            review_status="pending",
            metadata_json="{}",
        )
        db.add(offline_event)
        alerts.append(
            (
                AlertMessage(
                    event_id=str(offline_event.id),
                    device_id=str(device.id),
                    device_name=device.name,
                    event_type="device_offline",
                    importance="high",
                    started_at=now.isoformat(),
                ),
                offline_event,
            )
        )
    else:
        alerts.append(
            (
                AlertMessage(
                    device_id=str(device.id),
                    device_name=device.name,
                    event_type="device_online",
                    importance="low",
                    started_at=now.isoformat(),
                ),
                None,
            )
        )


async def _handle_state_message(db, device: Device, payload: str, alerts: list) -> None:
    now = datetime.now(timezone.utc)
    device.last_seen_at = now
    if device.status != "online":
        device.status = "online"

    state = extract_binary_state(payload)
    event_type, subtype = event_type_for_state(device.device_type, state, payload)
    importance = importance_for_event_type(event_type)

    event = Event(
        id=uuid.uuid4(),
        device_id=device.id,
        event_type=event_type,
        subtype=subtype,
        started_at=now,
        confidence=1.0 if state is not None else 0.0,
        importance=importance,
        review_status="pending",
        metadata_json="{}",
    )
    db.add(event)
    alerts.append(
        (
            AlertMessage(
                event_id=str(event.id),
                device_id=str(device.id),
                device_name=device.name,
                event_type=event_type,
                subtype=subtype,
                importance=importance,
                confidence=event.confidence,
                started_at=now.isoformat(),
            ),
            event,
        )
    )


async def mqtt_ingest_drain_loop() -> None:
    """Polls MqttManager's message queue, matches messages to configured
    Devices by topic, persists an Event (or a status transition) for
    each, then fans alerts out after commit — mirroring
    motion_event_drain_loop's commit-then-alert ordering."""
    logger.info("MQTT ingest drain loop started")

    while True:
        try:
            messages = mqtt_manager.drain_messages()
            if messages:
                async with async_session_factory() as db:
                    try:
                        devices = await _load_enabled_devices(db)
                        alerts: list[tuple[AlertMessage, Event | None]] = []

                        for message in messages:
                            device = _match_device(message, devices)
                            if device is None:
                                continue
                            if is_status_topic(message["topic"]):
                                await _handle_status_message(db, device, message["payload"], alerts)
                            else:
                                await _handle_state_message(db, device, message["payload"], alerts)

                        await db.commit()
                        if alerts:
                            logger.info("Persisted %d sensor event(s)", len(alerts))

                        for alert, related_event in alerts:
                            try:
                                await dispatch_event_alert(db, alert)
                                if related_event is not None:
                                    related_event.alerted = True
                                    await db.commit()
                            except Exception as exc:
                                logger.warning("Failed to dispatch sensor alert: %s", exc)
                    except Exception as exc:
                        await db.rollback()
                        logger.error("Failed to persist sensor events: %s", exc, exc_info=True)
        except Exception as exc:
            logger.error("MQTT ingest drain loop error: %s", exc, exc_info=True)

        await asyncio.sleep(INGEST_INTERVAL_SECONDS)
