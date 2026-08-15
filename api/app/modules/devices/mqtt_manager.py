"""
MqttManager — thread-safe singleton that owns the single MQTT client
connection used to ingest ESPHome and Zigbee2MQTT sensor events.

Mirrors the singleton-manager pattern used elsewhere in this codebase
(CaptureManager, RecordingManager, ConnectionManager): a ``__new__``-based
singleton whose background work happens on a dedicated thread (paho-mqtt's
own network loop thread, via ``loop_start()``), while consumers drain a
plain list guarded by a ``threading.Lock`` from the asyncio event loop.
This keeps MQTT I/O off the event loop without needing an async MQTT
client library.
"""

import logging
import threading
import time
from typing import Optional

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


class MqttManager:
    _instance: Optional["MqttManager"] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self._client: mqtt.Client | None = None
        self._connected = False
        self._messages: list[dict] = []
        self._queue_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    # ── lifecycle ──

    def start(
        self,
        host: str,
        port: int,
        username: str = "",
        password: str = "",
        topic_prefixes: list[str] | None = None,
    ) -> None:
        """Connect and subscribe in the background. Safe to call once at
        app startup; a no-op if already started."""
        if self._client is not None:
            return

        client = mqtt.Client()
        if username:
            client.username_pw_set(username, password or None)
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect
        self._topic_prefixes = topic_prefixes or []

        try:
            client.connect_async(host, port, keepalive=30)
        except Exception as exc:
            logger.warning("MQTT connect_async failed (host=%s port=%s): %s", host, port, exc)
            return

        client.loop_start()
        self._client = client
        logger.info("MQTT manager started (host=%s port=%s)", host, port)

    def stop(self) -> None:
        if self._client is None:
            return
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception as exc:
            logger.debug("MQTT disconnect error (ignored during shutdown): %s", exc)
        self._client = None
        self._connected = False
        logger.info("MQTT manager stopped")

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ── paho callbacks (run on paho's own network thread) ──

    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            logger.warning("MQTT connect failed, rc=%s", rc)
            return
        self._connected = True
        for prefix in getattr(self, "_topic_prefixes", []):
            client.subscribe(f"{prefix}/#")
            logger.info("MQTT subscribed: %s/#", prefix)

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            logger.warning("MQTT disconnected unexpectedly, rc=%s", rc)

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8", errors="replace")
        except Exception:
            payload = ""
        with self._queue_lock:
            self._messages.append(
                {"topic": msg.topic, "payload": payload, "received_at": time.time()}
            )

    # ── drain (called from the async event loop) ──

    def drain_messages(self) -> list[dict]:
        with self._queue_lock:
            drained, self._messages = self._messages, []
        return drained


mqtt_manager = MqttManager()
