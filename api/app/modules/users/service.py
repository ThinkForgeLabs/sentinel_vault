import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.modules.auth.model import User
from app.modules.users.schemas import SelfUpdate, UserCreate, UserUpdate

# NOTE: app.services.audit is imported lazily (inside functions) below —
# audit -> settings.service -> users.service, so a top-level import here
# would be circular.


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


async def get_user(db: AsyncSession, user_id: uuid.UUID | str) -> User:
    # Accept either a parsed UUID (the normal FastAPI path-param case) or a
    # raw string, since the id column is a native UUID and str values need
    # converting before hitting the driver's UUID bind processor.
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except (ValueError, AttributeError, TypeError):
            raise NotFoundError("User", user_id)

    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError("User", str(user_id))
    return user


async def create_user(
    db: AsyncSession, data: UserCreate, actor_id: str | None = None
) -> User:
    from app.services.audit import log_action

    existing = await db.execute(select(User).where(User.username == data.username))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(f"Username '{data.username}' already exists")

    user = User(
        username=data.username,
        display_name=data.display_name,
        password_hash=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    await db.flush()

    await log_action(
        db,
        actor_id=actor_id,
        action="create_user",
        resource_type="user",
        resource_id=str(user.id),
        details={"username": user.username, "role": user.role},
    )

    return user


async def update_user(
    db: AsyncSession, user_id: uuid.UUID | str, data: UserUpdate, actor_id: str | None = None
) -> User:
    from app.services.audit import log_action

    user = await get_user(db, user_id)
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(user, key, value)
    await db.flush()

    await log_action(
        db,
        actor_id=actor_id,
        action="update_user",
        resource_type="user",
        resource_id=str(user.id),
        details={"fields": list(updates.keys())},
    )

    return user


async def update_self(db: AsyncSession, user: User, data: SelfUpdate) -> User:
    """Self-service profile/password update. Never touches role or
    is_active — those stay owner-gated via update_user."""
    from app.services.audit import log_action

    password_changed = False
    if data.display_name is not None:
        user.display_name = data.display_name

    if data.new_password is not None:
        if not data.current_password or not verify_password(
            data.current_password, user.password_hash
        ):
            raise BadRequestError("Current password is incorrect")
        user.password_hash = hash_password(data.new_password)
        password_changed = True

    await db.flush()

    await log_action(
        db,
        actor_id=str(user.id),
        action="change_password" if password_changed else "update_self",
        resource_type="user",
        resource_id=str(user.id),
    )

    return user


async def delete_user(
    db: AsyncSession, user_id: uuid.UUID | str, actor_id: str | None = None
) -> None:
    from app.services.audit import log_action

    user = await get_user(db, user_id)

    if user.role == "owner":
        result = await db.execute(
            select(User).where(User.role == "owner", User.id != user.id)
        )
        if result.scalar_one_or_none() is None:
            raise ConflictError("Cannot delete the last owner account")

    deleted_id = str(user.id)
    deleted_username = user.username

    await db.delete(user)
    await db.flush()

    await log_action(
        db,
        actor_id=actor_id,
        action="delete_user",
        resource_type="user",
        resource_id=deleted_id,
        details={"username": deleted_username},
    )