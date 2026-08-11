import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.modules.auth.model import User
from app.modules.users.schemas import SelfUpdate, UserCreate, UserUpdate


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


async def create_user(db: AsyncSession, data: UserCreate) -> User:
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
    return user


async def update_user(db: AsyncSession, user_id: uuid.UUID | str, data: UserUpdate) -> User:
    user = await get_user(db, user_id)
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(user, key, value)
    await db.flush()
    return user


async def update_self(db: AsyncSession, user: User, data: SelfUpdate) -> User:
    """Self-service profile/password update. Never touches role or
    is_active — those stay owner-gated via update_user."""
    if data.display_name is not None:
        user.display_name = data.display_name

    if data.new_password is not None:
        if not data.current_password or not verify_password(
            data.current_password, user.password_hash
        ):
            raise BadRequestError("Current password is incorrect")
        user.password_hash = hash_password(data.new_password)

    await db.flush()
    return user


async def delete_user(db: AsyncSession, user_id: uuid.UUID | str) -> None:
    user = await get_user(db, user_id)

    if user.role == "owner":
        result = await db.execute(
            select(User).where(User.role == "owner", User.id != user.id)
        )
        if result.scalar_one_or_none() is None:
            raise ConflictError("Cannot delete the last owner account")

    await db.delete(user)
    await db.flush()