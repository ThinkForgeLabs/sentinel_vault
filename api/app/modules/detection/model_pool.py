"""
Multi-model YOLO pool — loads and caches several models simultaneously,
keyed by resolved file path, so different cameras can run different
models concurrently (e.g. one camera on the bundled stock model, another
on a user-uploaded custom model).

Ported from ThinkForgeLabs/ODDS (odds-v3) detection/model_pool.py, trimmed
of the legacy YOLOEngine compat layer since Sentinel Vault has no old
call sites to keep working — DetectionResult now lives here instead of a
separate engine.py.
"""

import logging
import threading
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    detections: list = field(default_factory=list)
    detected: bool = False
    frame_processed: bool = False
    snapshot_jpeg: Optional[bytes] = None


class _PooledModel:
    """Wraps a single loaded YOLO model with its own inference lock."""

    __slots__ = ("model", "path", "class_names", "lock")

    def __init__(self, model, path: str, class_names: dict):
        self.model = model
        self.path = path
        self.class_names = class_names
        self.lock = threading.Lock()


class ModelPool:
    """
    Thread-safe singleton that keeps multiple YOLO models loaded at once,
    keyed by their resolved file path. Cameras reference a model by path
    and can share the same loaded model instance without re-loading it.
    """

    _instance: Optional["ModelPool"] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self._models: dict[str, _PooledModel] = {}
        self._pool_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> "ModelPool":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    # ── lifecycle ──────────────────────────────────────────

    def load(self, path: str) -> None:
        """Load (or no-op if already loaded) a model by file path."""
        with self._pool_lock:
            if path in self._models:
                return
        from ultralytics import YOLO

        model = YOLO(path)
        class_names = dict(model.names) if hasattr(model, "names") else {}
        pooled = _PooledModel(model=model, path=path, class_names=class_names)
        with self._pool_lock:
            self._models[path] = pooled
        logger.info("ModelPool: loaded %s (classes=%s)", path, class_names)

    def unload(self, path: str) -> None:
        with self._pool_lock:
            removed = self._models.pop(path, None)
        if removed:
            logger.info("ModelPool: unloaded %s", path)

    def is_loaded(self, path: str) -> bool:
        with self._pool_lock:
            return path in self._models

    def class_names(self, path: str) -> dict:
        with self._pool_lock:
            pooled = self._models.get(path)
        return dict(pooled.class_names) if pooled else {}

    def loaded_paths(self) -> list[str]:
        with self._pool_lock:
            return list(self._models.keys())

    # ── inference ──────────────────────────────────────────

    def detect(
        self,
        path: str,
        frame: np.ndarray,
        confidence: float = 0.5,
        class_ids: Optional[list[int]] = None,
    ) -> DetectionResult:
        """
        Run inference on a single frame using the model at `path`.
        If `class_ids` is non-empty, only detections whose class_id is in
        that list are returned (this is what powers the "detect up to 3
        classes" per-camera feature end to end).
        """
        import cv2

        with self._pool_lock:
            pooled = self._models.get(path)

        if pooled is None:
            return DetectionResult()

        with pooled.lock:
            try:
                results = pooled.model(frame, verbose=False, conf=confidence)
            except Exception as exc:
                logger.error("ModelPool inference error (%s): %s", path, exc)
                return DetectionResult()

        detections: list[dict] = []
        detected = False
        class_filter = set(class_ids) if class_ids else None

        for r in results:
            if not r.boxes or len(r.boxes) == 0:
                continue

            data = (
                r.boxes.data.cpu().numpy()
                if hasattr(r.boxes, "data")
                else r.boxes.cpu().numpy()
            )
            for i, box in enumerate(data):
                if len(box) >= 6:
                    x1, y1, x2, y2, conf, cls = box[:6]
                elif len(box) >= 4:
                    x1, y1, x2, y2 = box[:4]
                    conf = float(r.boxes.conf[i]) if hasattr(r.boxes, "conf") else 0.0
                    cls = int(r.boxes.cls[i]) if hasattr(r.boxes, "cls") else -1
                else:
                    continue

                if float(conf) < confidence:
                    continue

                class_id = int(cls)
                if class_filter is not None and class_id not in class_filter:
                    continue

                detections.append(
                    {
                        "bbox": tuple(map(int, [x1, y1, x2, y2])),
                        "confidence": round(float(conf), 3),
                        "class_id": class_id,
                        "class_name": pooled.class_names.get(
                            class_id, f"class_{class_id}"
                        ),
                    }
                )
                detected = True

        snapshot = None
        if detected:
            _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            snapshot = buf.tobytes()

        return DetectionResult(
            detections=detections,
            detected=detected,
            frame_processed=True,
            snapshot_jpeg=snapshot,
        )


model_pool = ModelPool.get_instance()
