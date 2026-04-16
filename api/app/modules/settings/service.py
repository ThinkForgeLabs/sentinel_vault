import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.model import AuditLog, SystemSetting
from app.modules.settings.schemas import SettingUpdate


async def get_all_settings(db: AsyncSession) -> list[SystemSetting]:
    result = await db.execute(select(SystemSetting).order_by(SystemSetting.key))
    return list(result.scalars().all())


async def get_setting(db: AsyncSession, key: str) -> SystemSetting | None:
    return await db.get(SystemSetting, key)


async def upsert_setting(db: AsyncSession, key: str, data: SettingUpdate) -> SystemSetting:
    existing = await get_setting(db, key)
    if existing:
        existing.value_json = data.value_json
        await db.flush()
        return existing
    else:
        setting = SystemSetting(key=key, value_json=data.value_json)
        db.add(setting)
        await db.flush()
        return setting


async def is_setup_complete(db: AsyncSession) -> bool:
    setting = await get_setting(db, "setup_complete")
    if setting is None:
        return False
    try:
        return json.loads(setting.value_json) == "true"
    except (json.JSONDecodeError, TypeError):
        return False


async def write_audit(
    db: AsyncSession,
    actor_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict | None = None,
) -> None:
    log = AuditLog(
        actor_user_id=actor_id,
        action_type=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details_json=json.dumps(details or {}),
    )
    db.add(log)