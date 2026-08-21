import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.modules.auth.model import User
from app.modules.devices.schemas import DeviceCreate, DeviceOut, DeviceUpdate
from app.modules.devices.service import (
    create_device,
    delete_device,
    get_device,
    list_devices,
    update_device,
)

router = APIRouter()


@router.get("", response_model=list[DeviceOut])
async def get_devices(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await list_devices(db)


@router.post("", response_model=DeviceOut, status_code=201)
async def add_device(
    body: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_device(db, body, actor_id=str(current_user.id))


@router.get("/{device_id}", response_model=DeviceOut)
async def get_device_detail(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await get_device(db, device_id)


@router.put("/{device_id}", response_model=DeviceOut)
async def edit_device(
    device_id: uuid.UUID,
    body: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_device(db, device_id, body, actor_id=str(current_user.id))


@router.delete("/{device_id}", status_code=204)
async def remove_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_device(db, device_id, actor_id=str(current_user.id))
