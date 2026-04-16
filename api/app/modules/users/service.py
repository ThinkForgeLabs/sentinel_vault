from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password
from app.modules.auth.model import User
from app.modules.users.schemas import UserCreate, UserUpdate


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


async def get_user(db: AsyncSession, user_id: str) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise NotFoundError("User", user_id)
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


async def update_user(db: AsyncSession, user_id: str, data: UserUpdate) -> User:
    user = await get_user(db, user_id)
    updates = data.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(user, key, value)
    await db.flush()
    return user