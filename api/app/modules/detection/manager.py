import logging
import threading
import numpy as np
from typing import Dict, Optional
from .motion import MotionDetector, MotionResult

logger = logging.getLogger(__name__)


class DetectionManager:
    """Thread-safe singleton that owns one MotionDetector per camera."""

    _instance: Optional["DetectionManager"] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self._detectors: Dict[str, MotionDetector] = {}
        self._detectors_lock = threading.Lock()
        self._call_counts: Dict[str, int] = {}
        self._miss_counts: Dict[str, int] = {}

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

    def register(self, camera_id, **config) -> MotionDetector:
        camera_id = str(camera_id)                        # ← normalize
        with self._detectors_lock:
            if camera_id in self._detectors:
                return self._detectors[camera_id]
            detector = MotionDetector(camera_id=camera_id, **config)
            self._detectors[camera_id] = detector
        logger.info(
            "Motion detector registered: camera=%s (total=%d, mgr_id=%s)",
            camera_id,
            len(self._detectors),
            id(self),
        )
        return detector

    def unregister(self, camera_id):
        camera_id = str(camera_id)                        # ← normalize
        with self._detectors_lock:
            removed = self._detectors.pop(camera_id, None)
            self._call_counts.pop(camera_id, None)
            self._miss_counts.pop(camera_id, None)
        if removed:
            logger.info("Motion detector unregistered: camera=%s", camera_id)

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
                "MOTION" if result else "None",
            )

        return result

    # ---- config ------------------------------------------------------ #

    def get_detector(self, camera_id) -> Optional[MotionDetector]:
        camera_id = str(camera_id)                        # ← normalize
        with self._detectors_lock:
            return self._detectors.get(camera_id)

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
    def all_detectors(self) -> Dict[str, MotionDetector]:
        with self._detectors_lock:
            return dict(self._detectors)