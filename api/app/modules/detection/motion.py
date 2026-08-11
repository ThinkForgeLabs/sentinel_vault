# app/modules/detection/motion.py

import cv2
import numpy as np
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MotionResult:
    total_area: float = 0.0
    bounding_boxes: list = field(default_factory=list)
    snapshot_jpeg: Optional[bytes] = None
    timestamp: float = 0.0


class MotionDetector:
    def __init__(
        self,
        camera_id: str,
        enabled: bool = True,
        threshold: int = 25,
        min_contour_area: int = 500,
        blur_kernel: int = 21,
        downscale_factor: float = 1.0,
        frame_skip: int = 0,
    ):
        self.camera_id = camera_id
        self.enabled = enabled
        self.threshold = threshold
        self.min_contour_area = min_contour_area
        self.blur_kernel = blur_kernel
        # Low-overhead knobs for constrained hardware (e.g. Raspberry Pi 5):
        # downscale_factor shrinks the frame before diffing (0.25-1.0), and
        # frame_skip processes only every Nth frame, leaving the rest
        # untouched to save CPU.
        self.downscale_factor = downscale_factor
        self.frame_skip = frame_skip

        self._prev_gray: Optional[np.ndarray] = None
        self._last_trigger: float = 0.0
        self._frame_count: int = 0
        self._debug_interval: int = 20

    def process_frame(self, frame: np.ndarray) -> Optional[MotionResult]:
        if not self.enabled:
            if self._frame_count == 0:
                logger.warning(
                    "Motion detector DISABLED for camera=%s", self.camera_id
                )
            self._frame_count += 1
            return None

        self._frame_count += 1

        # ── Frame skip: only run the (relatively expensive) diff pipeline
        #    every Nth frame. Skipped frames are simply ignored rather than
        #    diffed against a stale reference, avoiding false positives
        #    from the larger time delta between compared frames. ──
        if self.frame_skip > 0 and (self._frame_count - 1) % (self.frame_skip + 1) != 0:
            return None

        scale = self.downscale_factor
        work_frame = frame
        if scale < 1.0:
            work_frame = cv2.resize(
                frame, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA
            )

        try:
            gray = cv2.cvtColor(work_frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(
                gray, (self.blur_kernel, self.blur_kernel), 0
            )
        except Exception as e:
            logger.error(
                "Frame conversion error: camera=%s shape=%s dtype=%s error=%s",
                self.camera_id, frame.shape, frame.dtype, e,
            )
            return None

        if self._prev_gray is None:
            self._prev_gray = gray.copy()
            logger.info(
                "Motion detector got first frame: camera=%s shape=%s",
                self.camera_id, gray.shape,
            )
            return None

        delta = cv2.absdiff(self._prev_gray, gray)
        self._prev_gray = gray.copy()

        _, thresh = cv2.threshold(
            delta, self.threshold, 255, cv2.THRESH_BINARY
        )
        thresh = cv2.dilate(thresh, None, iterations=2)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # min_contour_area is expressed in full-resolution pixels; when
        # working on a downscaled frame, contour areas shrink by scale^2,
        # so scale the comparison threshold down to match rather than
        # changing detection sensitivity as a side effect of performance
        # tuning.
        effective_min_area = self.min_contour_area * (scale ** 2)
        significant = [
            c for c in contours
            if cv2.contourArea(c) >= effective_min_area
        ]

        # ── Periodic debug stats ──
        if self._frame_count % self._debug_interval == 0:
            max_delta = int(delta.max()) if delta.size > 0 else 0
            mean_delta = float(delta.mean()) if delta.size > 0 else 0.0
            thresh_pixels = int(cv2.countNonZero(thresh))
            logger.info(
                "Detection stats: camera=%s frame=%d max_delta=%d "
                "mean_delta=%.1f thresh_pixels=%d contours=%d "
                "significant=%d threshold=%d min_area=%d enabled=%s",
                self.camera_id, self._frame_count, max_delta,
                mean_delta, thresh_pixels, len(contours),
                len(significant), self.threshold, self.min_contour_area,
                self.enabled,
            )

        if not significant:
            return None

        # ── No cooldown here — clip lifecycle in recording_manager
        #    handles timing (pre-roll / post-roll / min duration) ──

        now = time.time()
        self._last_trigger = now

        # Areas/boxes were computed on the (possibly downscaled) work
        # frame; scale them back up to full-resolution coordinates so
        # downstream consumers (overlays, clip cropping) don't need to
        # know the detector's internal scale factor.
        inv_scale = 1.0 / scale if scale > 0 else 1.0
        total_area = sum(cv2.contourArea(c) for c in significant) * (inv_scale ** 2)
        bounding_boxes = [
            [int(round(v * inv_scale)) for v in cv2.boundingRect(c)]
            for c in significant
        ]

        # Snapshot is always encoded from the original full-resolution
        # frame, never the downscaled working copy, so alert thumbnails
        # stay sharp regardless of the performance tuning in effect.
        _, jpeg_buf = cv2.imencode(
            ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85]
        )

        logger.info(
            "Motion detected: camera=%s area=%.0f regions=%d",
            self.camera_id, total_area, len(significant),
        )

        return MotionResult(
            total_area=total_area,
            bounding_boxes=bounding_boxes,
            snapshot_jpeg=jpeg_buf.tobytes(),
            timestamp=now,
        )

    def reset(self):
        self._prev_gray = None
        self._last_trigger = 0.0
        self._frame_count = 0

    @property
    def frames_processed(self) -> int:
        return self._frame_count

    @property
    def last_trigger_time(self) -> float:
        return self._last_trigger