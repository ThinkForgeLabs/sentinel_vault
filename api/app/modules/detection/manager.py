import logging
import threading
from typing import Dict, Optional, Union

import numpy as np

from .detector import YoloDetector
from .motion import MotionDetector, MotionResult

logger = logging.getLogger(__name__)

Detector = Union[MotionDetector, YoloDetector]


class DetectionManager:
    """Thread-safe singleton that owns one detector (motion or yolo) per camera."""

    _instance: Optional["DetectionManager"] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self._detectors: Dict[str, Detector] = {}
        self._backends: Dict[str, str] = {}
        self._detectors_lock = threading.Lock()
        self._call_counts: Dict[str, int] = {}
        self._miss_counts: Dict[str, int] = {}

        self._alerts_lock = threading.Lock()
        self._pending_alerts: list = []

    @classmethod
    def get_instance(cls) -> "DetectionManager":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
                    logger.info(
                        "DetectionManager singleton created (id=%s)",
                        id(cls._instance),
                    )
        return cls._instance

    # ---- lifecycle --------------------------------------------------- #

    def register(self, camera_id, backend: str = "motion", **config) -> Detector:
        """
        Register a detector for a camera. `backend` picks the implementation
        ("motion" default, or "yolo") — no-ops (returns the existing detector
        unchanged) if the camera is already registered, matching the prior
        behavior. Use `sync_camera()` instead to replace an existing
        detector, e.g. when switching backends or reloading settings.
        """
        camera_id = str(camera_id)                        # ← normalize
        with self._detectors_lock:
            if camera_id in self._detectors:
                return self._detectors[camera_id]
            detector = self._build_detector(camera_id, backend, config)
            self._detectors[camera_id] = detector
            self._backends[camera_id] = backend
        logger.info(
            "%s detector registered: camera=%s (total=%d, mgr_id=%s)",
            backend, camera_id, len(self._detectors), id(self),
        )
        return detector

    def sync_camera(self, camera_id, backend: str, **config) -> Detector:
        """Replace (or create) the detector for a camera with fresh config —
        used when detection settings change or the backend is switched."""
        camera_id = str(camera_id)                        # ← normalize
        with self._detectors_lock:
            detector = self._build_detector(camera_id, backend, config)
            self._detectors[camera_id] = detector
            self._backends[camera_id] = backend
        logger.info("Detector synced: camera=%s backend=%s", camera_id, backend)
        return detector

    def _build_detector(self, camera_id: str, backend: str, config: dict) -> Detector:
        if backend == "yolo":
            config = dict(config)
            config.setdefault("on_alert", self.push_alert)
            return YoloDetector(camera_id=camera_id, **config)
        return MotionDetector(camera_id=camera_id, **config)

    def unregister(self, camera_id):
        camera_id = str(camera_id)                        # ← normalize
        with self._detectors_lock:
            removed = self._detectors.pop(camera_id, None)
            self._backends.pop(camera_id, None)
            self._call_counts.pop(camera_id, None)
            self._miss_counts.pop(camera_id, None)
        if removed:
            logger.info("Detector unregistered: camera=%s", camera_id)

    # ---- per-frame --------------------------------------------------- #

    def process_frame(
        self, camera_id, frame: np.ndarray
    ) -> Optional[MotionResult]:
        camera_id = str(camera_id)                        # ← normalize
        with self._detectors_lock:
            detector = self._detectors.get(camera_id)

        if detector is None:
            count = self._miss_counts.get(camera_id, 0) + 1
            self._miss_counts[camera_id] = count
            if count <= 3 or count % 100 == 0:
                logger.warning(
                    "No detector for camera=%s (miss #%d, "
                    "registered=%s, mgr_id=%s)",
                    camera_id,
                    count,
                    list(self._detectors.keys()),
                    id(self),
                )
            return None

        count = self._call_counts.get(camera_id, 0) + 1
        self._call_counts[camera_id] = count

        if count == 1:
            logger.info(
                "First detection call WITH detector: camera=%s "
                "frame_shape=%s dtype=%s mgr_id=%s",
                camera_id,
                frame.shape,
                frame.dtype,
                id(self),
            )

        result = detector.process_frame(frame)

        if count <= 3 or count % 50 == 0:
            logger.info(
                "Detection call #%d: camera=%s result=%s",
                count,
                camera_id,
                "DETECTED" if result else "None",
            )

        return result

    # ---- alerts (yolo backend only) ----------------------------------- #

    def push_alert(self, alert: dict) -> None:
        """Called from a recorder thread (via YoloDetector.on_alert) — queues
        a pending detection alert for the async drain loop to persist as an
        Event, the same 'capture on a thread, sync via queue' pattern used
        by RecordingManager elsewhere in this codebase."""
        with self._alerts_lock:
            self._pending_alerts.append(alert)

    def drain_alerts(self) -> list:
        with self._alerts_lock:
            drained, self._pending_alerts = self._pending_alerts, []
        return drained

    # ---- config ------------------------------------------------------ #

    def get_detector(self, camera_id) -> Optional[Detector]:
        camera_id = str(camera_id)                        # ← normalize
        with self._detectors_lock:
            return self._detectors.get(camera_id)

    def get_backend(self, camera_id) -> Optional[str]:
        camera_id = str(camera_id)                        # ← normalize
        with self._detectors_lock:
            return self._backends.get(camera_id)

    def update_config(self, camera_id, **kwargs):
        camera_id = str(camera_id)                        # ← normalize
        with self._detectors_lock:
            detector = self._detectors.get(camera_id)
        if detector is None:
            return
        for key, value in kwargs.items():
            if hasattr(detector, key) and not key.startswith("_"):
                setattr(detector, key, value)
        logger.info(
            "Detector config updated: camera=%s %s", camera_id, kwargs
        )

    @property
    def all_detectors(self) -> Dict[str, Detector]:
        with self._detectors_lock:
            return dict(self._detectors)
