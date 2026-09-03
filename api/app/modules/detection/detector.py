# app/modules/detection/detector.py
"""
YoloDetector — real ML object detection backend, ported/adapted from
ThinkForgeLabs/ODDS (odds-v3) detection/manager.py's per-camera inference
logic, stripped of the Kalman tracker, target-designation, and monocular
range/bearing geolocation (per product scope decision — detection only,
no tracker).

Deliberately mirrors MotionDetector's public contract
(process_frame/reset/frames_processed/last_trigger_time, returning an
Optional[MotionResult]) so DetectionManager.process_frame() and its only
caller, recording_manager.py's _CameraRecorder.run(), need zero changes.
`total_area` is filled with the summed pixel area of detection bounding
boxes so the existing importance heuristic in recording_manager.py
("medium" if confidence > 5000 else "low") stays meaningful without any
change on that side.

Alert dispatch (MQTT JSON + CoT XML for TAK) happens here, cooldown-gated,
using metadata (camera name/location/lat/lon/publish flags) captured at
registration time — the detector itself never talks to the database.
When an alert fires, `on_alert` (wired by DetectionManager) is invoked with
a plain dict so the async event loop can persist it as an Event, the same
"capture on a thread, sync via queue" pattern used elsewhere in this
codebase.
"""

import logging
import time
import uuid
from typing import Callable, Optional

import numpy as np

from app.core.config import settings as app_settings
from app.services.cot_builder import build_detection_cot
from app.services.mqtt_service import mqtt_service

from .model_pool import model_pool
from .motion import MotionResult

logger = logging.getLogger(__name__)


class YoloDetector:
    def __init__(
        self,
        camera_id: str,
        enabled: bool = True,
        model_path: Optional[str] = None,
        confidence: float = 0.5,
        class_ids: Optional[list[int]] = None,
        alert_enabled: bool = True,
        alert_cooldown: float = 30.0,
        camera_name: str = "",
        location_label: str = "",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        mqtt_publish_enabled: bool = False,
        cot_publish_enabled: bool = False,
        on_alert: Optional[Callable[[dict], None]] = None,
    ):
        self.camera_id = camera_id
        self.enabled = enabled
        self.model_path = model_path
        self.confidence = confidence
        self.class_ids = class_ids or []
        self.alert_enabled = alert_enabled
        self.alert_cooldown = alert_cooldown

        self.camera_name = camera_name
        self.location_label = location_label
        self.latitude = latitude
        self.longitude = longitude
        self.mqtt_publish_enabled = mqtt_publish_enabled
        self.cot_publish_enabled = cot_publish_enabled
        self.on_alert = on_alert

        self._last_trigger: float = 0.0
        self._last_alert: float = 0.0
        self._frame_count: int = 0
        self._detection_count: int = 0

        if self.model_path:
            try:
                model_pool.load(self.model_path)
            except Exception as exc:
                logger.error(
                    "YoloDetector: failed to load model %s for camera=%s: %s",
                    self.model_path, self.camera_id, exc,
                )

    def process_frame(self, frame: np.ndarray) -> Optional[MotionResult]:
        if not self.enabled or not self.model_path:
            self._frame_count += 1
            return None

        self._frame_count += 1

        result = model_pool.detect(
            self.model_path, frame, confidence=self.confidence, class_ids=self.class_ids
        )

        if not result.detected:
            return None

        self._detection_count += 1
        now = time.time()
        self._last_trigger = now

        boxes = [d["bbox"] for d in result.detections]
        total_area = sum(max(0, x2 - x1) * max(0, y2 - y1) for (x1, y1, x2, y2) in boxes)
        bounding_boxes = [[x1, y1, x2 - x1, y2 - y1] for (x1, y1, x2, y2) in boxes]

        logger.info(
            "YOLO detection: camera=%s classes=%s regions=%d",
            self.camera_id,
            [d["class_name"] for d in result.detections],
            len(result.detections),
        )

        if self._should_dispatch_alert():
            self._dispatch_alert(result.detections, now, result.snapshot_jpeg)

        return MotionResult(
            total_area=float(total_area),
            bounding_boxes=bounding_boxes,
            snapshot_jpeg=result.snapshot_jpeg,
            timestamp=now,
        )

    # ── alert dispatch (MQTT + CoT/TAK, cooldown-gated) ───────────────── #

    def _should_dispatch_alert(self) -> bool:
        if not self.alert_enabled:
            return False
        now = time.time()
        if now - self._last_alert < self.alert_cooldown:
            return False
        self._last_alert = now
        return True

    def _dispatch_alert(self, detections: list[dict], timestamp: float, snapshot_jpeg) -> None:
        best = max(detections, key=lambda d: d["confidence"]) if detections else None
        class_names = [d["class_name"] for d in detections]

        alert = {
            "alert_id": str(uuid.uuid4()),
            "camera_id": self.camera_id,
            "camera_name": self.camera_name,
            "location_label": self.location_label,
            "class_names": class_names,
            "confidence": best["confidence"] if best else 0.0,
            "detections": detections,
            "timestamp": timestamp,
            "snapshot_jpeg": snapshot_jpeg,
        }

        if self.mqtt_publish_enabled:
            try:
                mqtt_service.publish_alert(
                    {k: v for k, v in alert.items() if k != "snapshot_jpeg"}
                )
            except Exception as exc:
                logger.error("Failed to publish MQTT alert for camera=%s: %s", self.camera_id, exc)

        has_position = self.latitude is not None and self.longitude is not None
        if self.cot_publish_enabled and has_position and best:
            try:
                xml = build_detection_cot(
                    camera_id=self.camera_id,
                    camera_name=self.camera_name,
                    latitude=self.latitude,
                    longitude=self.longitude,
                    class_name=best["class_name"],
                    confidence=best["confidence"],
                    cot_type=app_settings.cot_type,
                    stale_seconds=app_settings.cot_stale_seconds,
                    location_label=self.location_label,
                )
                mqtt_service.publish_cot(xml)
            except Exception as exc:
                logger.error("Failed to publish CoT event for camera=%s: %s", self.camera_id, exc)

        if self.on_alert:
            try:
                self.on_alert(alert)
            except Exception as exc:
                logger.error("on_alert callback failed for camera=%s: %s", self.camera_id, exc)

    def reset(self):
        self._last_trigger = 0.0
        self._last_alert = 0.0
        self._frame_count = 0
        self._detection_count = 0

    @property
    def frames_processed(self) -> int:
        return self._frame_count

    @property
    def detection_count(self) -> int:
        return self._detection_count

    @property
    def last_trigger_time(self) -> float:
        return self._last_trigger
