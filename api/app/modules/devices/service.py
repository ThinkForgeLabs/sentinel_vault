import uuid

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.devices.model import Device
from app.modules.devices.schemas import DeviceCreate, DeviceUpdate
from app.services.audit import log_action


async def list_devices(db: AsyncSession) -> list[Device]:
    result = await db.execute(select(Device).order_by(Device.created_at))
    return list(result.scalars().all())


async def get_device(db: AsyncSession, device_id: uuid.UUID) -> Device:
    device = await db.get(Device, device_id)
    if device is None:
        raise NotFoundError("Device", device_id)
    return device


async def create_device(
    db: AsyncSession, data: DeviceCreate, actor_id: str | None = None
) -> Device:
    device = Device(
        name=data.name,
        device_type=data.device_type,
        location_label=data.location_label,
        protocol=data.protocol,
        mqtt_topic=data.mqtt_topic,
        enabled=data.enabled,
        status="offline",
    )
    db.add(device)
    await db.flush()

    await log_action(
        db,
        actor_id=actor_id,
        action="create_device",
        resource_type="device",
        resource_id=str(device.id),
        details={
            "name": device.name,
            "device_type": device.device_type,
            "protocol": device.protocol,
        },
    )

    return device


async def update_device(
    db: AsyncSession, device_id: uuid.UUID, data: DeviceUpdate, actor_id: str | None = None
) -> Device:
    device = await get_device(db, device_id)
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(device, key, value)
    await db.flush()

    await log_action(
        db,
        actor_id=actor_id,
        action="update_device",
        resource_type="device",
        resource_id=str(device_id),
        details={"fields": list(updates.keys())},
    )

    return device


async def delete_device(
    db: AsyncSession, device_id: uuid.UUID, actor_id: str | None = None
) -> None:
    device = await get_device(db, device_id)
    device_name = device.name
    dev_id = device.id

    # Bulk-delete dependent Event rows first — mirrors delete_camera's
    # approach in app/modules/cameras/service.py (bypasses the ORM identity
    # map so this can never be tripped up by relationship/backref quirks).
    from app.modules.events.model import Event

    await db.execute(sa_delete(Event).where(Event.device_id == dev_id))

    await db.delete(device)
    await db.flush()

    await log_action(
        db,
        actor_id=actor_id,
        action="delete_device",
        resource_type="device",
        resource_id=str(dev_id),
        details={"name": device_name},
    )
