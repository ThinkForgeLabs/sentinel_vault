import cv2
import numpy as np
import threading
import time
from typing import Optional


class CaptureManager:
    """Opens each device ONCE in a background thread, shares JPEG frames."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst._devices: dict = {}
                    cls._instance = inst
        return cls._instance

    def _device_key(self, source: str) -> str:
        if source.startswith("usb://"):
            return f"usb:{source.replace('usb://', '')}"
        return source

    def get_active_sources(self) -> set[str]:
        """Return the set of source URLs currently being captured."""
        with self._lock:
            return {dev["source"] for dev in self._devices.values()}

    def get_frame(self, source: str) -> Optional[bytes]:
        """Return latest JPEG bytes (or None). Starts capture on first call."""
        key = self._device_key(source)
        with self._lock:
            if key not in self._devices:
                self._devices[key] = {
                    "source": source,
                    "frame": None,
                    "jpeg": None,
                    "last_access": time.time(),
                    "stop": False,
                    "thread": None,
                    "ready": threading.Event(),
                }
                t = threading.Thread(
                    target=self._capture_loop, args=(key,), daemon=True
                )
                self._devices[key]["thread"] = t
                t.start()

        dev = self._devices[key]
        dev["last_access"] = time.time()

        # Wait up to 5s for first frame
        dev["ready"].wait(timeout=5.0)
        return dev["jpeg"]

    def get_raw_frame(self, source: str) -> Optional[np.ndarray]:
        """Return latest raw numpy frame (or None). Starts capture if needed."""
        key = self._device_key(source)
        need_start = False
        with self._lock:
            if key not in self._devices:
                need_start = True

        if need_start:
            self.get_frame(source)  # starts capture and waits for first frame

        dev = self._devices.get(key)
        if dev is None:
            return None
        dev["last_access"] = time.time()
        return dev.get("frame")

    def release_all(self):
        with self._lock:
            for dev in self._devices.values():
                dev["stop"] = True
            self._devices.clear()

    def _capture_loop(self, key: str):
        dev = self._devices[key]
        source = dev["source"]

        # Open capture
        if source.startswith("usb://"):
            index = int(source.replace("usb://", ""))
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(source)

        if not cap.isOpened():
            dev["ready"].set()
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        # Warmup for USB cameras
        if source.startswith("usb://"):
            for _ in range(30):
                cap.read()

        try:
            while not dev["stop"]:
                ret, frame = cap.read()
                if ret:
                    dev["frame"] = frame.copy()
                    _, buf = cv2.imencode(
                        ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70]
                    )
                    dev["jpeg"] = buf.tobytes()
                    dev["ready"].set()
                else:
                    time.sleep(0.1)

                # Auto-stop if no one watching for 30s
                if time.time() - dev["last_access"] > 30:
                    break

                time.sleep(0.033)  # ~30 fps cap
        finally:
            cap.release()
            with self._lock:
                self._devices.pop(key, None)


capture_manager = CaptureManager()