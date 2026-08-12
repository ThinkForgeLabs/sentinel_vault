import json
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.core.exceptions import ConflictError
from app.core.security import create_access_token, create_refresh_token
from app.modules.auth.model import User
from app.modules.settings.model import AuditLog, SystemSetting
from app.modules.settings.schemas import SettingUpdate, SetupInitRequest
from app.modules.users.schemas import UserCreate
from app.modules.users.service import create_user

# NOTE: imported lazily (inside functions) where used below — app.services.audit
# imports write_audit from this module, so a top-level import here would be circular.


async def get_all_settings(db: AsyncSession) -> list[SystemSetting]:
    result = await db.execute(select(SystemSetting).order_by(SystemSetting.key))
    return list(result.scalars().all())


async def get_setting(db: AsyncSession, key: str) -> SystemSetting | None:
    return await db.get(SystemSetting, key)


async def upsert_setting(
    db: AsyncSession, key: str, data: SettingUpdate, actor_id: str | None = None
) -> SystemSetting:
    from app.services.audit import log_action

    existing = await get_setting(db, key)
    if existing:
        existing.value_json = data.value_json
        await db.flush()
        result = existing
    else:
        setting = SystemSetting(key=key, value_json=data.value_json)
        db.add(setting)
        await db.flush()
        result = setting

    if actor_id is not None:
        await log_action(
            db,
            actor_id=actor_id,
            action="update_setting",
            resource_type="setting",
            resource_id=key,
        )

    return result


async def is_setup_complete(db: AsyncSession) -> bool:
    setting = await get_setting(db, "setup_complete")
    if setting is None:
        return False
    try:
        return json.loads(setting.value_json) == "true"
    except (json.JSONDecodeError, TypeError):
        return False


async def complete_setup(db: AsyncSession, data: SetupInitRequest) -> tuple[User, str, str, int]:
    """First-run bootstrap: create the initial owner account and mark setup
    complete. Only allowed when setup hasn't run yet *and* no users exist
    yet, so a seeded/demo install can't be silently re-initialized."""
    if await is_setup_complete(db):
        raise ConflictError("Setup has already been completed")

    existing = await db.execute(select(User.id).limit(1))
    if existing.first() is not None:
        raise ConflictError("Setup has already been completed")

    owner = await create_user(
        db,
        UserCreate(
            username=data.admin_username,
            display_name=data.admin_display_name,
            password=data.admin_password,
            role="owner",
        ),
    )

    await upsert_setting(db, "storage_path", SettingUpdate(value_json=json.dumps(data.storage_path)))
    await upsert_setting(
        db, "encryption_enabled", SettingUpdate(value_json=json.dumps(data.encryption_enabled))
    )
    await upsert_setting(db, "setup_complete", SettingUpdate(value_json=json.dumps("true")))

    access = create_access_token(str(owner.id), {"role": owner.role})
    refresh = create_refresh_token(str(owner.id))
    expires_in = app_settings.access_token_expire_minutes * 60

    from app.services.audit import log_action

    await log_action(
        db,
        actor_id=str(owner.id),
        action="setup_complete",
        resource_type="system",
        resource_id=str(owner.id),
        details={"admin_username": data.admin_username},
    )

    await db.flush()
    return owner, access, refresh, expires_in


async def write_audit(
    db: AsyncSession,
    actor_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict | None = None,
) -> None:
    # actor_user_id is a native UUID column -- callers pass str(user.id) for
    # convenience, so parse it here. Falls back to None for a malformed/
    # missing actor rather than failing the whole request over a logging
    # detail.
    actor_uuid = None
    if actor_id is not None:
        try:
            actor_uuid = uuid.UUID(str(actor_id))
        except (ValueError, AttributeError, TypeError):
            actor_uuid = None

    log = AuditLog(
        actor_user_id=actor_uuid,
        action_type=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details_json=json.dumps(details or {}),
    )
    db.add(log)