import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_device(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/devices",
        json={
            "name": "Front Door Presence",
            "device_type": "presence_sensor",
            "location_label": "Front Porch",
            "protocol": "esphome",
            "mqtt_topic": "esphome/front-door/binary_sensor/presence/state",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Front Door Presence"
    assert data["status"] == "offline"
    assert data["enabled"] is True


@pytest.mark.asyncio
async def test_list_devices(client: AsyncClient, auth_headers):
    await client.post(
        "/api/v1/devices",
        json={
            "name": "Back Door Sensor",
            "device_type": "door_sensor",
            "protocol": "zigbee2mqtt",
            "mqtt_topic": "zigbee2mqtt/Back Door Sensor",
        },
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/devices", headers=auth_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_update_delete_device(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/devices",
        json={
            "name": "Doorbell Button",
            "device_type": "doorbell_button",
            "protocol": "esphome",
            "mqtt_topic": "esphome/doorbell/button/press/state",
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    device_id = create_resp.json()["id"]

    get_resp = await client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Doorbell Button"

    put_resp = await client.put(
        f"/api/v1/devices/{device_id}",
        json={"name": "Front Doorbell Button", "enabled": False},
        headers=auth_headers,
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["name"] == "Front Doorbell Button"
    assert put_resp.json()["enabled"] is False

    delete_resp = await client.delete(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    missing_resp = await client.get(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert missing_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_device_not_found(client: AsyncClient, auth_headers):
    import uuid

    resp = await client.get(f"/api/v1/devices/{uuid.uuid4()}", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_device_cascades_events(client: AsyncClient, auth_headers, db_session):
    """Deleting a device must remove its Events too — mirrors delete_camera's
    manual bulk-delete precedent (the SQLite test DB doesn't enforce FK
    ON DELETE CASCADE without PRAGMA foreign_keys=ON)."""
    import uuid
    from datetime import datetime, timezone

    from app.modules.events.model import Event

    create_resp = await client.post(
        "/api/v1/devices",
        json={
            "name": "Window Sensor",
            "device_type": "window_sensor",
            "protocol": "zigbee2mqtt",
            "mqtt_topic": "zigbee2mqtt/Window Sensor",
        },
        headers=auth_headers,
    )
    device_id = create_resp.json()["id"]

    event = Event(
        id=uuid.uuid4(),
        device_id=uuid.UUID(device_id),
        event_type="window_open",
        started_at=datetime.now(timezone.utc),
        importance="medium",
        review_status="pending",
        metadata_json="{}",
    )
    db_session.add(event)
    await db_session.commit()

    delete_resp = await client.delete(f"/api/v1/devices/{device_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    events_resp = await client.get(
        "/api/v1/events", params={"device_id": device_id}, headers=auth_headers
    )
    assert events_resp.status_code == 200
    assert events_resp.json() == []
