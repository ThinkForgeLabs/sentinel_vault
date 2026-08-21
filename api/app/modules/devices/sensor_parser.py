"""
Pure functions that turn a raw MQTT (topic, payload) pair into a sensor
event decision. Kept dependency-free (no DB, no network) so they can be
unit tested without a broker — see tests/test_mqtt_ingest.py.
"""

import json

# Truthy/"open"/"active" state keys published by ESPHome and Zigbee2MQTT
# for the sensor types we care about. Zigbee2MQTT's `contact` is inverted
# (True == closed) so it's handled separately below.
_PRESENCE_KEYS = ("presence", "occupancy")
_CONTACT_KEY = "contact"
_BUTTON_KEYS = ("action", "state")

# importance per resulting event_type — mirrors the "high" importance used
# for camera_offline elsewhere in the codebase (app/modules/recordings/tasks.py).
IMPORTANCE_BY_EVENT_TYPE = {
    "doorbell_pressed": "high",
    "door_open": "medium",
    "window_open": "medium",
    "presence_detected": "medium",
    "door_closed": "low",
    "window_closed": "low",
    "presence_cleared": "low",
    "device_offline": "high",
    "sensor_state": "low",
}


def is_status_topic(topic: str) -> bool:
    """ESPHome publishes availability on `<node>/status`; Zigbee2MQTT
    publishes it on `<device>/availability` (when the bridge option is
    enabled). Either suffix marks a connectivity ping rather than sensor
    state."""
    lowered = topic.rstrip("/").lower()
    return lowered.endswith("/status") or lowered.endswith("/availability")


def status_topic_base(topic: str) -> str:
    """Strips the trailing '/status' or '/availability' segment, e.g.
    'esphome/front-door/status' -> 'esphome/front-door'."""
    stripped = topic.rstrip("/")
    parts = stripped.rsplit("/", 1)
    return parts[0] if len(parts) == 2 else stripped


def device_matches_status_topic(device_mqtt_topic: str, status_base: str) -> bool:
    """True if a device's configured state topic falls under a status/
    availability topic's base — e.g. device topic
    'esphome/front-door/binary_sensor/presence/state' matches status base
    'esphome/front-door', and Zigbee2MQTT's exact-topic devices match
    when the base equals the device topic itself."""
    return device_mqtt_topic == status_base or device_mqtt_topic.startswith(status_base + "/")


def parse_status_payload(payload: str) -> str | None:
    """Returns 'online' / 'offline', or None if unrecognized."""
    text = payload.strip().lower()
    if text in ("online", "true", "1"):
        return "online"
    if text in ("offline", "false", "0"):
        return "offline"
    try:
        data = json.loads(payload)
        if isinstance(data, dict) and "state" in data:
            return parse_status_payload(str(data["state"]))
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _parse_payload(payload: str) -> dict | str:
    """JSON object if the payload parses as one, else the raw string."""
    try:
        data = json.loads(payload)
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, TypeError):
        pass
    return payload


def _truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().upper() in ("ON", "TRUE", "1", "OPEN", "DETECTED")
    return False


def extract_binary_state(payload: str) -> bool | None:
    """Best-effort boolean reading of a sensor state payload, independent
    of device type. Returns None if nothing recognizable was found."""
    parsed = _parse_payload(payload)

    if isinstance(parsed, dict):
        if _CONTACT_KEY in parsed:
            # Zigbee2MQTT convention: contact == True means the door/window
            # is CLOSED. Invert so True consistently means "triggered/open".
            return not _truthy(parsed[_CONTACT_KEY])
        for key in _PRESENCE_KEYS:
            if key in parsed:
                return _truthy(parsed[key])
        for key in _BUTTON_KEYS:
            if key in parsed:
                val = parsed[key]
                if isinstance(val, str):
                    return val.strip().lower() not in ("", "off", "idle", "none")
                return _truthy(val)
        return None

    # Plain-text payload, e.g. ESPHome's default binary_sensor state topic.
    return _truthy(parsed)


def event_type_for_state(
    device_type: str, state: bool | None, raw_payload: str
) -> tuple[str, str | None]:
    """Maps a device_type + resolved boolean state to (event_type, subtype).
    Falls back to a generic 'sensor_state' event carrying the raw payload
    as subtype when the state can't be confidently interpreted."""
    if state is None:
        return "sensor_state", raw_payload[:100]

    if device_type == "presence_sensor":
        return ("presence_detected", None) if state else ("presence_cleared", None)
    if device_type == "door_sensor":
        return ("door_open", None) if state else ("door_closed", None)
    if device_type == "window_sensor":
        return ("window_open", None) if state else ("window_closed", None)
    if device_type == "doorbell_button":
        # Momentary contact — every truthy reading is a fresh press.
        return ("doorbell_pressed", None) if state else ("sensor_state", raw_payload[:100])

    return "sensor_state", raw_payload[:100]


def importance_for_event_type(event_type: str) -> str:
    return IMPORTANCE_BY_EVENT_TYPE.get(event_type, "low")
