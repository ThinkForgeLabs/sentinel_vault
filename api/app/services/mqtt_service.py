"""
Optional MQTT bridge for external MQTT/TAK integration.

Ported from ThinkForgeLabs/ODDS (odds-v3) app/services/mqtt_service.py,
trimmed of track-update publishing (no Kalman tracker in this port) —
keeps JSON alert publishing and Cursor-on-Target (CoT) XML publishing
for TAK Server / ATAK / WinTAK / FreeTAKServer ingestion.
"""

import json
import logging
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class MQTTService:
    _instance: Optional["MQTTService"] = None

    def __init__(self):
        self._client = None
        self._connected = False
        self._enabled = settings.mqtt_enabled

    @classmethod
    def get_instance(cls) -> "MQTTService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def start(self):
        if not self._enabled:
            logger.info("MQTT disabled in config")
            return

        try:
            import paho.mqtt.client as mqtt

            self._client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION2,
                client_id="sentinel-vault-backend",
            )
            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect

            if settings.mqtt_username:
                self._client.username_pw_set(
                    settings.mqtt_username, settings.mqtt_password or None
                )

            if settings.mqtt_tls_enabled:
                import ssl

                self._client.tls_set(
                    cert_reqs=ssl.CERT_NONE if settings.mqtt_tls_insecure else ssl.CERT_REQUIRED
                )
                if settings.mqtt_tls_insecure:
                    self._client.tls_insecure_set(True)

            self._client.connect_async(settings.mqtt_broker, settings.mqtt_port)
            self._client.loop_start()
            logger.info(
                "MQTT connecting to %s:%d (tls=%s)",
                settings.mqtt_broker,
                settings.mqtt_port,
                settings.mqtt_tls_enabled,
            )
        except ImportError:
            logger.warning("paho-mqtt not installed — MQTT disabled")
            self._enabled = False
        except Exception as exc:
            logger.error("MQTT start error: %s", exc)

    def stop(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            logger.info("MQTT stopped")

    def publish_alert(self, alert: dict):
        if not self._connected or not self._client:
            return
        try:
            payload = json.dumps(alert, default=str)
            self._client.publish(settings.mqtt_topic_alerts, payload, qos=1)
        except Exception as exc:
            logger.error("MQTT publish alert error: %s", exc)

    def publish_cot(self, cot_xml: str, topic: Optional[str] = None):
        """
        Publish a raw Cursor-on-Target XML event for TAK ingestion. Unlike
        publish_alert() (JSON), this topic carries plain CoT XML text — the
        format PyTAK / FreeTAKServer / most TAK MQTT bridges expect on a
        `mqtt://host:port/topic` feed.
        """
        if not self._connected or not self._client:
            return
        try:
            self._client.publish(topic or settings.mqtt_topic_cot, cot_xml, qos=1)
        except Exception as exc:
            logger.error("MQTT publish CoT error: %s", exc)

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        self._connected = True
        logger.info("MQTT connected (rc=%s)", rc)

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        self._connected = False
        logger.warning("MQTT disconnected (rc=%s)", rc)


mqtt_service = MQTTService.get_instance()
