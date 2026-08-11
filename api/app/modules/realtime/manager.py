# app/modules/realtime/manager.py
"""
ConnectionManager — thread-safe singleton that owns every live WebSocket
connection and fans alert payloads out to all of them.

Mirrors the singleton-manager pattern used by CaptureManager elsewhere in
this codebase (``__new__``-based singleton + module-level instance), but
since WebSocket I/O only ever happens on the asyncio event loop, the
connection set is guarded by an ``asyncio.Lock`` rather than a
``threading.Lock``.
"""

import asyncio
import logging
import threading
from typing import Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    _instance: Optional["ConnectionManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    inst = super().__new__(cls)
                    inst._connections = set()
                    inst._async_lock = asyncio.Lock()
                    cls._instance = inst
        return cls._instance

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._async_lock:
            self._connections.add(websocket)
        logger.info("WebSocket client connected (total=%d)", len(self._connections))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._async_lock:
            self._connections.discard(websocket)
        logger.info("WebSocket client disconnected (total=%d)", len(self._connections))

    async def broadcast(self, message: dict) -> None:
        """Send a JSON-serializable message to every connected client.
        Dead sockets are pruned silently — a slow/closed client must never
        raise and block the caller (recording/detection threads' async
        drain loop)."""
        async with self._async_lock:
            targets = list(self._connections)
        if not targets:
            return

        dead: list[WebSocket] = []
        for ws in targets:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)

        if dead:
            async with self._async_lock:
                for ws in dead:
                    self._connections.discard(ws)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


connection_manager = ConnectionManager()
