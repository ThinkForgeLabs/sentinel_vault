# app/modules/realtime/router.py

import logging

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_owner
from app.modules.auth.model import User

from . import service
from .manager import connection_manager
from .schemas import AlertSettingsRead, AlertSettingsUpdate, ConnectionStatus

logger = logging.getLogger(__name__)
router = APIRouter()


@router.websocket("/ws")
async def alerts_websocket(websocket: WebSocket, token: str = Query(...)):
    """Real-time alert channel. Clients authenticate with their normal JWT
    access token passed as a query param (browsers can't set custom
    WebSocket headers), then receive a JSON message for every new event or
    camera status change until they disconnect."""
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        await websocket.close(code=4401)
        return

    await connection_manager.connect(websocket)
    try:
        while True:
            # Clients don't need to send anything meaningful — this just
            # keeps the coroutine alive until the socket closes so we can
            # detect disconnects and clean up.
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.debug("WebSocket loop ended: %s", exc)
    finally:
        await connection_manager.disconnect(websocket)


@router.get("/status", response_model=ConnectionStatus)
async def realtime_status(_: User = Depends(get_current_user)):
    return ConnectionStatus(connected_clients=connection_manager.connection_count)


@router.get("/settings", response_model=AlertSettingsRead)
async def read_alert_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.get_alert_settings(db)


@router.put("/settings", response_model=AlertSettingsRead)
async def write_alert_settings(
    body: AlertSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_owner),
):
    return await service.update_alert_settings(db, body)
