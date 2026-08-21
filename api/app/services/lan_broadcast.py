# app/services/lan_broadcast.py
"""
LAN broadcast — the "local network" alert channel.

Fires a JSON UDP datagram to the subnet broadcast address so any other
device on the same local network (a script, a smart display, a second
Sentinel Vault instance, etc.) can react to alerts without any pairing or
discovery protocol on our side. This is intentionally fire-and-forget:
failures are logged and swallowed, since a missing LAN channel must never
block the WebSocket alert or the DB write that triggered it.
"""

import asyncio
import json
import logging
import socket

logger = logging.getLogger(__name__)

DEFAULT_PORT = 37020


def send_broadcast(payload: dict, port: int = DEFAULT_PORT) -> bool:
    """Blocking UDP send — always call via ``send_broadcast_async`` from
    async code (or ``asyncio.to_thread`` directly) so the event loop is
    never blocked on socket I/O."""
    try:
        data = json.dumps(payload).encode("utf-8")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(data, ("255.255.255.255", port))
        return True
    except OSError as exc:
        logger.warning("LAN broadcast failed (port=%d): %s", port, exc)
        return False


async def send_broadcast_async(payload: dict, port: int = DEFAULT_PORT) -> bool:
    return await asyncio.to_thread(send_broadcast, payload, port)
