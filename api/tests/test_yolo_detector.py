"""Unit tests for the YOLO detection backend — detector/manager/cot/mqtt.

These deliberately avoid loading a real ultralytics model (not a project
dependency for the test environment; model_pool.load() lazily imports
ultralytics only when actually invoked). Instead they monkeypatch
model_pool.detect()/model_pool.load() so YoloDetector's own logic (the
MotionResult-compatibility conversion, cooldown gating, alert payload
shape) is exercised directly.
"""
import time

import numpy as np
import pytest

from app.modules.detection.detector import YoloDetector
from app.modules.detection.manager import DetectionManager
from app.modules.detection.model_pool import DetectionResult, model_pool
from app.services.cot_builder import build_detection_cot


@pytest.fixture(autouse=True)
def _stub_model_load(monkeypatch):
    """Never touch the real ultralytics/YOLO loader in unit tests."""
    monkeypatch.setattr(model_pool, "load", lambda path: None)
    yield


def _fake_detection_result(detected=True):
    if not detected:
        return DetectionResult(detections=[], detected=False, frame_processed=True)
    return DetectionResult(
        detections=[
            {"bbox": (10, 10, 60, 90), "confidence": 0.82, "class_id": 0, "class_name": "person"},
            {"bbox": (100, 40, 140, 70), "confidence": 0.55, "class_id": 2, "class_name": "car"},
        ],
        detected=True,
        frame_processed=True,
        snapshot_jpeg=b"fake-jpeg-bytes",
    )


def test_process_frame_no_model_path_is_noop():
    detector = YoloDetector(camera_id="cam-1", enabled=True, model_path=None)
    result = detector.process_frame(np.zeros((10, 10, 3), dtype=np.uint8))
    assert result is None
    assert detector.frames_processed == 1


def test_process_frame_disabled_is_noop(monkeypatch):
    monkeypatch.setattr(model_pool, "detect", lambda *a, **k: _fake_detection_result())
    detector = YoloDetector(camera_id="cam-2", enabled=False, model_path="yolov8n.pt")
    result = detector.process_frame(np.zeros((10, 10, 3), dtype=np.uint8))
    assert result is None


def test_process_frame_produces_motionresult_compatible_output(monkeypatch):
    monkeypatch.setattr(model_pool, "detect", lambda *a, **k: _fake_detection_result())
    detector = YoloDetector(
        camera_id="cam-3", enabled=True, model_path="yolov8n.pt", alert_enabled=False
    )
    result = detector.process_frame(np.zeros((10, 10, 3), dtype=np.uint8))
    assert result is not None

    # recording_manager.py only ever reads .total_area and .snapshot_jpeg —
    # both must be present and correctly derived from the bbox detections.
    expected_area = (60 - 10) * (90 - 10) + (140 - 100) * (70 - 40)
    assert result.total_area == pytest.approx(expected_area)
    assert result.snapshot_jpeg == b"fake-jpeg-bytes"
    assert result.bounding_boxes == [[10, 10, 50, 80], [100, 40, 40, 30]]
    assert detector.detection_count == 1
    assert detector.last_trigger_time > 0


def test_process_frame_no_detection_returns_none(monkeypatch):
    monkeypatch.setattr(
        model_pool, "detect", lambda *a, **k: _fake_detection_result(detected=False)
    )
    detector = YoloDetector(camera_id="cam-4", enabled=True, model_path="yolov8n.pt")
    result = detector.process_frame(np.zeros((10, 10, 3), dtype=np.uint8))
    assert result is None
    assert detector.detection_count == 0


def test_alert_dispatch_respects_cooldown_and_calls_on_alert(monkeypatch):
    monkeypatch.setattr(model_pool, "detect", lambda *a, **k: _fake_detection_result())
    alerts = []
    detector = YoloDetector(
        camera_id="cam-5",
        enabled=True,
        model_path="yolov8n.pt",
        alert_enabled=True,
        alert_cooldown=60.0,
        camera_name="Front Door",
        on_alert=alerts.append,
    )

    detector.process_frame(np.zeros((10, 10, 3), dtype=np.uint8))
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["camera_id"] == "cam-5"
    assert alert["camera_name"] == "Front Door"
    assert set(alert["class_names"]) == {"person", "car"}
    assert alert["confidence"] == pytest.approx(0.82)  # best/highest-confidence detection

    # Second frame within the cooldown window must NOT dispatch again.
    detector.process_frame(np.zeros((10, 10, 3), dtype=np.uint8))
    assert len(alerts) == 1


def test_alert_dispatch_fires_again_after_cooldown(monkeypatch):
    monkeypatch.setattr(model_pool, "detect", lambda *a, **k: _fake_detection_result())
    alerts = []
    detector = YoloDetector(
        camera_id="cam-6",
        enabled=True,
        model_path="yolov8n.pt",
        alert_enabled=True,
        alert_cooldown=0.01,
        on_alert=alerts.append,
    )
    detector.process_frame(np.zeros((10, 10, 3), dtype=np.uint8))
    time.sleep(0.02)
    detector.process_frame(np.zeros((10, 10, 3), dtype=np.uint8))
    assert len(alerts) == 2


def test_manager_dispatches_yolo_backend_and_wires_on_alert(monkeypatch):
    monkeypatch.setattr(model_pool, "detect", lambda *a, **k: _fake_detection_result())
    mgr = DetectionManager.get_instance()
    mgr.unregister("cam-manager-yolo")

    detector = mgr.register(
        "cam-manager-yolo", backend="yolo", model_path="yolov8n.pt", alert_cooldown=0.0
    )
    assert isinstance(detector, YoloDetector)
    assert mgr.get_backend("cam-manager-yolo") == "yolo"

    mgr.process_frame("cam-manager-yolo", np.zeros((10, 10, 3), dtype=np.uint8))
    drained = mgr.drain_alerts()
    assert len(drained) == 1
    assert drained[0]["camera_id"] == "cam-manager-yolo"

    mgr.unregister("cam-manager-yolo")


def test_manager_sync_camera_switches_backend(monkeypatch):
    monkeypatch.setattr(model_pool, "detect", lambda *a, **k: _fake_detection_result())
    mgr = DetectionManager.get_instance()
    mgr.unregister("cam-switch")

    mgr.register("cam-switch", backend="motion")
    assert mgr.get_backend("cam-switch") == "motion"

    mgr.sync_camera("cam-switch", backend="yolo", model_path="yolov8n.pt")
    assert mgr.get_backend("cam-switch") == "yolo"
    assert isinstance(mgr.get_detector("cam-switch"), YoloDetector)

    mgr.unregister("cam-switch")


def test_cot_xml_contains_expected_fields():
    xml = build_detection_cot(
        camera_id="cam-7",
        camera_name="Gate Camera",
        latitude=32.7767,
        longitude=-96.7970,
        class_name="person",
        confidence=0.91,
        cot_type="a-u-G",
        stale_seconds=60.0,
        location_label="North Fence",
    )
    assert '<?xml version="1.0"' in xml
    assert 'type="a-u-G"' in xml
    assert 'lat="32.7767000"' in xml
    assert 'lon="-96.7970000"' in xml
    assert "person" in xml
    assert "Gate Camera" in xml
    assert "North Fence" in xml
    # No range/bearing/track_id fields — dropped from this port per scope.
    assert "track_id" not in xml
    assert "bearing" not in xml


def test_mqtt_service_noop_when_disabled():
    from app.services.mqtt_service import MQTTService

    svc = MQTTService()  # fresh instance, not the module singleton
    assert svc.is_enabled is False
    svc.start()  # should log and return, not raise
    svc.publish_alert({"foo": "bar"})  # not connected -> no-op, not raise
    svc.publish_cot("<event/>")  # not connected -> no-op, not raise
    svc.stop()  # no client -> no-op, not raise
