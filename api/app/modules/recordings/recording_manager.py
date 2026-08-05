"""
RecordingManager — owns one background thread per camera that:
  1. pulls raw frames from CaptureManager
  2. writes them to rotating video segments on disk
  3. feeds frames through DetectionManager for motion
  4. builds motion clips (pre-roll + post-roll) when motion fires

Completed segments and motion events are pushed onto thread-safe queues
that the async event loop drains periodically (see tasks.py) to persist
them to the database — the same "capture on a thread, sync via queue"
pattern used by CaptureManager and DetectionManager elsewhere in this
codebase.
"""

import datetime as dt
import logging
import threading
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Optional

import cv2

from app.core.config import settings
from app.modules.cameras.capture_manager import capture_manager
from app.modules.detection.manager import DetectionManager
from app.services.storage import get_clip_path, get_segment_path, get_thumbnail_path

logger = logging.getLogger(__name__)

SEGMENT_FOURCC = "XVID"
SEGMENT_EXT = ".avi"
# get_clip_path() in app/services/storage.py hardcodes a .mp4 suffix,
# so the clip writer must use an MP4-compatible codec.
CLIP_FOURCC = "mp4v"

FPS = 15.0
FRAME_INTERVAL = 1.0 / FPS

PRE_ROLL_SECONDS = 5
POST_ROLL_SECONDS = 5
MIN_CLIP_SECONDS = 2

# How long a camera can go without a frame before it's considered offline.
OFFLINE_AFTER_SECONDS = 15


class _CameraRecorder:
    """State + loop for a single camera's recording thread."""

    def __init__(self, camera_id: str, source: str, retention_days: int):
        self.camera_id = camera_id
        self.source = source
        self.retention_days = retention_days
        self.stop_flag = False
        self.thread: Optional[threading.Thread] = None

        self._segment_writer: Optional[cv2.VideoWriter] = None
        self._segment_path: Optional[Path] = None
        self._segment_start: float = 0.0
        self._frame_size: Optional[tuple[int, int]] = None

        self._pre_roll: deque = deque(maxlen=int(PRE_ROLL_SECONDS * FPS))
        self._clip_writer: Optional[cv2.VideoWriter] = None
        self._clip_path: Optional[Path] = None
        self._clip_id: Optional[str] = None
        self._clip_start: float = 0.0
        self._clip_last_motion: float = 0.0
        self._clip_confidence: float = 0.0
        self._clip_thumb: Optional[bytes] = None

        self._last_frame_at: float = 0.0
        self._was_online: Optional[bool] = None

    # ── segment lifecycle ──────────────────────────────────────────

    def _open_segment(self, frame) -> None:
        h, w = frame.shape[:2]
        self._frame_size = (w, h)
        segment_name = f"{uuid.uuid4()}{SEGMENT_EXT}"
        self._segment_path = get_segment_path(self.camera_id, segment_name)
        fourcc = cv2.VideoWriter_fourcc(*SEGMENT_FOURCC)
        self._segment_writer = cv2.VideoWriter(str(self._segment_path), fourcc, FPS, (w, h))
        self._segment_start = time.time()

    def _close_segment(self) -> Optional[dict]:
        if self._segment_writer is None or self._segment_path is None:
            return None

        self._segment_writer.release()
        end = time.time()
        duration = max(end - self._segment_start, 0.0)
        segment_path = self._segment_path
        self._segment_writer = None
        self._segment_path = None

        if duration < 1.0 or not segment_path.exists():
            segment_path.unlink(missing_ok=True)
            return None

        file_size = segment_path.stat().st_size
        resolution = f"{self._frame_size[0]}x{self._frame_size[1]}" if self._frame_size else ""

        return {
            "id": uuid.uuid4(),
            "camera_id": self.camera_id,
            "start_time": self._segment_start,
            "end_time": end,
            "file_path": str(segment_path),
            "file_size": file_size,
            "duration_seconds": duration,
            "resolution": resolution,
            "status": "complete",
        }

    # ── motion clip lifecycle ──────────────────────────────────────

    def _start_clip(self, frame, motion_result) -> None:
        h, w = frame.shape[:2]
        self._clip_id = str(uuid.uuid4())
        self._clip_path = get_clip_path(self._clip_id)
        fourcc = cv2.VideoWriter_fourcc(*CLIP_FOURCC)
        self._clip_writer = cv2.VideoWriter(str(self._clip_path), fourcc, FPS, (w, h))

        # Flush pre-roll buffer first so the clip captures the lead-up.
        for buffered in self._pre_roll:
            self._clip_writer.write(buffered)

        self._clip_start = time.time() - (len(self._pre_roll) * FRAME_INTERVAL)
        self._clip_last_motion = time.time()
        self._clip_confidence = motion_result.total_area
        self._clip_thumb = motion_result.snapshot_jpeg

    def _extend_clip(self, motion_result) -> None:
        self._clip_last_motion = time.time()
        self._clip_confidence = max(self._clip_confidence, motion_result.total_area)

    def _close_clip(self) -> Optional[dict]:
        if self._clip_writer is None:
            return None

        self._clip_writer.release()
        end = self._clip_last_motion + POST_ROLL_SECONDS
        duration = max(end - self._clip_start, 0.0)
        clip_path = self._clip_path
        clip_id = self._clip_id
        thumb_bytes = self._clip_thumb
        confidence = self._clip_confidence

        self._clip_writer = None
        self._clip_path = None
        self._clip_id = None
        self._clip_thumb = None
        self._clip_confidence = 0.0

        if duration < MIN_CLIP_SECONDS or clip_path is None or not clip_path.exists():
            if clip_path:
                clip_path.unlink(missing_ok=True)
            return None

        thumbnail_path = None
        if thumb_bytes:
            thumbnail_path = get_thumbnail_path(clip_id)
            try:
                thumbnail_path.write_bytes(thumb_bytes)
            except OSError as exc:
                logger.warning("Failed writing thumbnail for %s: %s", clip_id, exc)
                thumbnail_path = None

        started_at = dt.datetime.fromtimestamp(self._clip_start, tz=dt.timezone.utc)
        ended_at = dt.datetime.fromtimestamp(end, tz=dt.timezone.utc)

        return {
            "id": uuid.UUID(clip_id),
            "camera_id": self.camera_id,
            "event_type": "motion",
            "subtype": "frame_diff",
            "started_at": started_at,
            "ended_at": ended_at,
            "confidence": confidence,
            "importance": "medium" if confidence > 5000 else "low",
            "thumbnail_path": str(thumbnail_path) if thumbnail_path else None,
            "clip_path": str(clip_path),
            "clip_duration_seconds": duration,
            "metadata": {},
        }

    # ── main loop ───────────────────────────────────────────────────

    def run(self, on_segment, on_event, on_status_change):
        detection_mgr = DetectionManager.get_instance()

        while not self.stop_flag:
            frame = capture_manager.get_raw_frame(self.source)

            if frame is None:
                self._handle_offline(on_status_change)
                time.sleep(0.5)
                continue

            self._handle_online(on_status_change)
            self._last_frame_at = time.time()

            if self._segment_writer is None:
                self._open_segment(frame)
            self._segment_writer.write(frame)

            elapsed = time.time() - self._segment_start
            if elapsed >= settings.segment_duration_minutes * 60:
                segment = self._close_segment()
                if segment:
                    on_segment(segment)

            self._pre_roll.append(frame.copy())

            motion_result = detection_mgr.process_frame(self.camera_id, frame)
            if motion_result is not None:
                if self._clip_writer is None:
                    self._start_clip(frame, motion_result)
                else:
                    self._extend_clip(motion_result)

            if self._clip_writer is not None:
                self._clip_writer.write(frame)
                if time.time() - self._clip_last_motion >= POST_ROLL_SECONDS:
                    event = self._close_clip()
                    if event:
                        on_event(event)

            time.sleep(FRAME_INTERVAL)

        # ── shutdown: flush whatever is in flight ──
        segment = self._close_segment()
        if segment:
            on_segment(segment)
        event = self._close_clip()
        if event:
            on_event(event)

    def _handle_offline(self, on_status_change) -> None:
        if self._last_frame_at and time.time() - self._last_frame_at < OFFLINE_AFTER_SECONDS:
            return
        if self._was_online is not False:
            self._was_online = False
            on_status_change(self.camera_id, "offline")

    def _handle_online(self, on_status_change) -> None:
        if self._was_online is not True:
            self._was_online = True
            on_status_change(self.camera_id, "online")


class RecordingManager:
    """Thread-safe singleton — one _CameraRecorder per recording-enabled camera."""

    _instance: Optional["RecordingManager"] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self._recorders: dict[str, _CameraRecorder] = {}
        self._recorders_lock = threading.Lock()

        self._completed_segments: list[dict] = []
        self._completed_events: list[dict] = []
        self._status_changes: list[tuple[str, str]] = []
        self._queue_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    # ── lifecycle ──

    def start_recording(self, camera_id: str, source: str, retention_days: int) -> None:
        camera_id = str(camera_id)
        with self._recorders_lock:
            if camera_id in self._recorders:
                return
            recorder = _CameraRecorder(camera_id, source, retention_days)
            self._recorders[camera_id] = recorder

        thread = threading.Thread(
            target=recorder.run,
            args=(self._on_segment, self._on_event, self._on_status_change),
            daemon=True,
            name=f"recorder-{camera_id}",
        )
        recorder.thread = thread
        thread.start()
        logger.info("Recording started: camera=%s", camera_id)

    def stop_recording(self, camera_id: str) -> None:
        camera_id = str(camera_id)
        with self._recorders_lock:
            recorder = self._recorders.pop(camera_id, None)
        if recorder:
            recorder.stop_flag = True
            logger.info("Recording stopping: camera=%s", camera_id)

    def stop_all(self) -> None:
        with self._recorders_lock:
            recorders = list(self._recorders.values())
            self._recorders.clear()
        for recorder in recorders:
            recorder.stop_flag = True

    def wait_for_threads(self, timeout: float) -> None:
        deadline = time.time() + timeout
        with self._recorders_lock:
            threads = [r.thread for r in self._recorders.values() if r.thread]
        for thread in threads:
            remaining = max(deadline - time.time(), 0)
            thread.join(timeout=remaining)

    # ── queue callbacks (called from recorder threads) ──

    def _on_segment(self, segment: dict) -> None:
        with self._queue_lock:
            self._completed_segments.append(segment)

    def _on_event(self, event: dict) -> None:
        with self._queue_lock:
            self._completed_events.append(event)

    def _on_status_change(self, camera_id: str, status: str) -> None:
        with self._queue_lock:
            self._status_changes.append((camera_id, status))

    # ── drain (called from the async event loop) ──

    def drain_completed(self) -> list[dict]:
        with self._queue_lock:
            drained, self._completed_segments = self._completed_segments, []
        return drained

    def drain_motion_events(self) -> list[dict]:
        with self._queue_lock:
            drained, self._completed_events = self._completed_events, []
        return drained

    def drain_status_changes(self) -> list[tuple[str, str]]:
        with self._queue_lock:
            drained, self._status_changes = self._status_changes, []
        return drained

    @property
    def active_camera_ids(self) -> set[str]:
        with self._recorders_lock:
            return set(self._recorders.keys())


recording_manager = RecordingManager()
