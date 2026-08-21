# app/modules/realtime/service.py

import json
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.schemas import SettingUpdate
from app.modules.settings.service import get_setting, upsert_setting

from .schemas import AlertSettingsRead, AlertSettingsUpdate

logger = logging.getLogger(__name__)

SETTINGS_KEY = "alert_settings"

DEFAULTS = {
    "websocket_enabled": True,
    "lan_broadcast_enabled": True,
    "lan_broadcast_port": 37020,
    "min_importance": "low",
}


async def get_alert_settings(db: AsyncSession) -> AlertSettingsRead:
    raw = await get_setting(db, SETTINGS_KEY)
    if raw:
        data = {**DEFAULTS, **json.loads(raw.value_json)}
    else:
        data = DEFAULTS.copy()
    return AlertSettingsRead(**data)


async def update_alert_settings(
    db: AsyncSession, update: AlertSettingsUpdate
) -> AlertSettingsRead:
    current = await get_alert_settings(db)
    merged = current.model_dump()

    for field_name, value in update.model_dump(exclude_unset=True).items():
        merged[field_name] = value

    await upsert_setting(db, SETTINGS_KEY, SettingUpdate(value_json=json.dumps(merged)))
    return AlertSettingsRead(**merged)
