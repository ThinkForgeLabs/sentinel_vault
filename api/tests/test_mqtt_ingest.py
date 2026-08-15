"""
Tests for the MQTT sensor-ingestion pure functions (app/modules/devices/
sensor_parser.py) and the async ingest loop's per-message handling
(app/modules/devices/ingest_task.py), exercised directly against fake
drained messages instead of a real broker connection.
"""

import uuid

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.modules.devices.ingest_task import (
    _handle_state_message,
    _handle_status_message,
    _match_device,
)
from app.modules.devices.model import Device
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

# ── sensor_parser pure functions ──


def test_is_status_topic():
    assert is_status_topic("esphome/front-door/status") is True
    assert is_status_topic("zigbee2mqtt/Back Door/availability") is True
    assert is_status_topic("esphome/front-door/binary_sensor/presence/state") is False


def test_status_topic_base():
    assert status_topic_base("esphome/front-door/status") == "esphome/front-door"
    assert status_topic_base("zigbee2mqtt/Back Door/availability") == "zigbee2mqtt/Back Door"


def test_device_matches_status_topic():
    assert device_matches_status_topic(
        "esphome/front-door/binary_sensor/presence/state", "esphome/front-door"
    )
    assert device_matches_status_topic("zigbee2mqtt/Back Door", "zigbee2mqtt/Back Door")
    assert not device_matches_status_topic(
        "esphome/other-node/binary_sensor/x/state", "esphome/front-door"
    )


@pytest.mark.parametrize(
    "payload,expected",
    [
        ("online", "online"),
        ("OFFLINE", "offline"),
        ('{"state": "online"}', "online"),
        ("garbage", None),
    ],
)
def test_parse_status_payload(payload, expected):
    assert parse_status_payload(payload) == expected


def test_extract_binary_state_zigbee_contact_inverted():
    # Zigbee2MQTT: contact=true means CLOSED, so it must map to False (not open).
    assert extract_binary_state('{"contact": true}') is False
    assert extract_binary_state('{"contact": false}') is True


def test_extract_binary_state_presence_json():
    assert extract_binary_state('{"presence": true}') is True
    assert extract_binary_state('{"occupancy": false}') is False


def test_extract_binary_state_plain_text():
    assert extract_binary_state("ON") is True
    assert extract_binary_state("OFF") is False


def test_extract_binary_state_unrecognized():
    assert extract_binary_state('{"unrelated_key": 42}') is None


@pytest.mark.parametrize(
    "device_type,state,expected_event_type",
    [
        ("presence_sensor", True, "presence_detected"),
        ("presence_sensor", False, "presence_cleared"),
        ("door_sensor", True, "door_open"),
        ("door_sensor", False, "door_closed"),
        ("window_sensor", True, "window_open"),
        ("window_sensor", False, "window_closed"),
        ("doorbell_button", True, "doorbell_pressed"),
    ],
)
def test_event_type_for_state(device_type, state, expected_event_type):
    event_type, _subtype = event_type_for_state(device_type, state, "raw")
    assert event_type == expected_event_type


def test_event_type_for_state_unknown_falls_back():
    event_type, subtype = event_type_for_state("presence_sensor", None, "weird-payload")
    assert event_type == "sensor_state"
    assert subtype == "weird-payload"


def test_importance_for_event_type():
    assert importance_for_event_type("doorbell_pressed") == "high"
    assert importance_for_event_type("door_open") == "medium"
    assert importance_for_event_type("door_closed") == "low"
    assert importance_for_event_type("totally_unknown") == "low"


# ── ingest_task message handling (DB-backed, no real broker) ──


@pytest_asyncio.fixture
async def door_device(db_session) -> Device:
    device = Device(
        id=uuid.uuid4(),
        name="Back Door Sensor",
        device_type="door_sensor",
        protocol="zigbee2mqtt",
        mqtt_topic="zigbee2mqtt/Back Door Sensor",
        status="offline",
        enabled=True,
        metadata_json="{}",
    )
    db_session.add(device)
    await db_session.commit()
    return device


def test_match_device_by_exact_topic(door_device):
    message = {"topic": "zigbee2mqtt/Back Door Sensor", "payload": "{}"}
    matched = _match_device(message, [door_device])
    assert matched is not None
    assert matched.id == door_device.id


def test_match_device_by_availability_topic(door_device):
    message = {"topic": "zigbee2mqtt/Back Door Sensor/availability", "payload": "online"}
    matched = _match_device(message, [door_device])
    assert matched is not None
    assert matched.id == door_device.id


def test_match_device_no_match(door_device):
    message = {"topic": "zigbee2mqtt/Unrelated Sensor", "payload": "{}"}
    assert _match_device(message, [door_device]) is None


@pytest.mark.asyncio
async def test_handle_state_message_creates_event(db_session, door_device):
    alerts = []
    await _handle_state_message(db_session, door_device, '{"contact": false}', alerts)
    await db_session.commit()

    result = await db_session.execute(select(Event).where(Event.device_id == door_device.id))
    events = list(result.scalars().all())
    assert len(events) == 1
    assert events[0].event_type == "door_open"
    assert events[0].device_id == door_device.id
    assert events[0].camera_id is None
    assert len(alerts) == 1
    assert alerts[0][0].device_id == str(door_device.id)
    assert alerts[0][0].event_type == "door_open"

    assert door_device.status == "online"


@pytest.mark.asyncio
async def test_handle_status_message_offline_creates_event(db_session, door_device):
    door_device.status = "online"
    alerts = []
    await _handle_status_message(db_session, door_device, "offline", alerts)
    await db_session.commit()

    result = await db_session.execute(select(Event).where(Event.device_id == door_device.id))
    events = list(result.scalars().all())
    assert len(events) == 1
    assert events[0].event_type == "device_offline"
    assert events[0].importance == "high"
    assert door_device.status == "offline"


@pytest.mark.asyncio
async def test_handle_status_message_online_no_event(db_session, door_device):
    door_device.status = "offline"
    alerts = []
    await _handle_status_message(db_session, door_device, "online", alerts)
    await db_session.commit()

    result = await db_session.execute(select(Event).where(Event.device_id == door_device.id))
    assert list(result.scalars().all()) == []
    assert len(alerts) == 1
    assert alerts[0][0].event_type == "device_online"
    assert door_device.status == "online"


@pytest.mark.asyncio
async def test_handle_status_message_same_status_is_noop(db_session, door_device):
    door_device.status = "online"
    alerts = []
    await _handle_status_message(db_session, door_device, "online", alerts)
    assert alerts == []
