import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_owner
from app.modules.auth.model import User
from app.modules.users.schemas import SelfUpdate, UserCreate, UserOut, UserUpdate
from app.modules.users.service import (
    create_user,
    delete_user,
    list_users,
    update_self,
    update_user,
)

router = APIRouter()


@router.put("/me", response_model=UserOut)
async def edit_self(
    body: SelfUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_self(db, current_user, body)


@router.get("", response_model=list[UserOut])
async def get_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_owner),
):
    return await list_users(db)


@router.post("", response_model=UserOut, status_code=201)
async def add_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    return await create_user(db, body, actor_id=str(current_user.id))


@router.put("/{user_id}", response_model=UserOut)
async def edit_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    return await update_user(db, user_id, body, actor_id=str(current_user.id))


@router.delete("/{user_id}", status_code=204)
async def remove_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    await delete_user(db, user_id, actor_id=str(current_user.id))