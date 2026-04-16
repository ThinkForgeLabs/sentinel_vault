from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_owner
from app.modules.auth.model import User
from app.modules.settings.schemas import (
    BulkSettingsUpdate,
    SettingOut,
    SettingUpdate,
    SetupStateResponse,
)
from app.modules.settings.service import (
    get_all_settings,
    is_setup_complete,
    upsert_setting,
)

router = APIRouter()


@router.get("", response_model=list[SettingOut])
async def read_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await get_all_settings(db)


@router.put("/{key}", response_model=SettingOut)
async def write_setting(
    key: str,
    body: SettingUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_owner),
):
    return await upsert_setting(db, key, body)


@router.put("", response_model=list[SettingOut])
async def write_bulk_settings(
    body: BulkSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_owner),
):
    results = []
    for key, value in body.settings.items():
        s = await upsert_setting(db, key, SettingUpdate(value_json=value))
        results.append(s)
    return results


@router.get("/setup/state", response_model=SetupStateResponse)
async def setup_state(db: AsyncSession = Depends(get_db)):
    complete = await is_setup_complete(db)
    return SetupStateResponse(
        complete=complete,
        step="complete" if complete else "welcome",
    )