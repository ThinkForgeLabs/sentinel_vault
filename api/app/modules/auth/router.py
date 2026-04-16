from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.modules.auth.model import User
from app.modules.auth.schemas import (
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserOut,
)
from app.modules.auth.service import authenticate, refresh_tokens

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await authenticate(db, body)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_tokens(db, body.refresh_token)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return user