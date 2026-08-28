import pytest
from httpx import AsyncClient


async def _create_camera(client: AsyncClient, auth_headers, **overrides) -> str:
    body = {
        "name": "Detection Test Cam",
        "rtsp_url": "rtsp://10.0.0.9/stream",
        "latitude": 32.7767,
        "longitude": -96.7970,
    }
    body.update(overrides)
    resp = await client.post("/api/v1/cameras", json=body, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()["id"]


@pytest.mark.asyncio
async def test_camera_create_stores_lat_lon(client: AsyncClient, auth_headers):
    camera_id = await _create_camera(client, auth_headers)
    resp = await client.get(f"/api/v1/cameras/{camera_id}", headers=auth_headers)
    data = resp.json()
    assert data["latitude"] == pytest.approx(32.7767)
    assert data["longitude"] == pytest.approx(-96.7970)
    # New detection defaults should be present and inert until opted in.
    assert data["detect_enabled"] is False
    assert data["detect_backend"] == "motion"
    assert data["detect_class_ids"] == []


@pytest.mark.asyncio
async def test_camera_rejects_invalid_lat_lon(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/cameras",
        json={
            "name": "Bad Coords Cam",
            "rtsp_url": "rtsp://10.0.0.9/stream",
            "latitude": 200.0,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_detection_settings_defaults(client: AsyncClient, auth_headers):
    camera_id = await _create_camera(client, auth_headers)
    resp = await client.get(
        f"/api/v1/detection/{camera_id}/detection-settings", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["detect_backend"] == "motion"
    assert data["detect_enabled"] is False
    assert data["confidence_threshold"] == pytest.approx(0.5)
    assert data["alert_cooldown_seconds"] == 30


@pytest.mark.asyncio
async def test_detection_settings_update_switches_to_yolo(
    client: AsyncClient, auth_headers, db_session
):
    from app.modules.detection.manager import DetectionManager
    from app.modules.ml_models.service import register_stock_model

    stock = await register_stock_model(
        db_session, "yolov8n.pt", class_names=["person", "car"], make_default=True
    )
    await db_session.commit()

    camera_id = await _create_camera(client, auth_headers)

    resp = await client.put(
        f"/api/v1/detection/{camera_id}/detection-settings",
        json={
            "detect_enabled": True,
            "detect_backend": "yolo",
            "model_id": str(stock.id),
            "confidence_threshold": 0.6,
            "detect_class_ids": [0, 2],
            "cot_publish_enabled": True,
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["detect_backend"] == "yolo"
    assert data["detect_enabled"] is True
    assert data["model_id"] == str(stock.id)
    assert data["confidence_threshold"] == pytest.approx(0.6)
    assert sorted(data["detect_class_ids"]) == [0, 2]
    assert data["cot_publish_enabled"] is True

    # Settings update should have re-registered the detector on the shared
    # DetectionManager singleton with the "yolo" backend for this camera.
    mgr = DetectionManager.get_instance()
    assert mgr.get_backend(camera_id) == "yolo"
    detector = mgr.get_detector(camera_id)
    assert detector is not None
    assert detector.confidence == pytest.approx(0.6)
    assert sorted(detector.class_ids) == [0, 2]


@pytest.mark.asyncio
async def test_detection_settings_rejects_bad_backend(client: AsyncClient, auth_headers):
    camera_id = await _create_camera(client, auth_headers)
    resp = await client.put(
        f"/api/v1/detection/{camera_id}/detection-settings",
        json={"detect_backend": "not-a-real-backend"},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_detection_settings_missing_camera_404(client: AsyncClient, auth_headers):
    import uuid

    resp = await client.get(
        f"/api/v1/detection/{uuid.uuid4()}/detection-settings", headers=auth_headers
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_engine_status_lists_cameras(client: AsyncClient, auth_headers):
    camera_id = await _create_camera(client, auth_headers, name="Status Cam")
    resp = await client.get("/api/v1/detection/engine/status", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert any(row["camera_id"] == camera_id for row in data)
