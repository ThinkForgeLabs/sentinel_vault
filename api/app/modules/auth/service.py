import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.modules.auth.model import User
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.services.audit import log_action, log_action_standalone


async def authenticate(db: AsyncSession, data: LoginRequest) -> TokenResponse:
    stmt = select(User).where(User.username == data.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not verify_password(data.password, user.password_hash):
        # log_action_standalone commits on its own connection so this row
        # survives the rollback get_db() triggers when UnauthorizedError
        # propagates out of this request.
        await log_action_standalone(
            actor_id=str(user.id) if user else None,
            action="login_failed",
            resource_type="auth",
            resource_id=data.username,
            details={"reason": "invalid_credentials"},
        )
        raise UnauthorizedError("Invalid username or password")

    if not user.is_active:
        await log_action_standalone(
            actor_id=str(user.id),
            action="login_failed",
            resource_type="auth",
            resource_id=data.username,
            details={"reason": "account_disabled"},
        )
        raise UnauthorizedError("Account is disabled")

    access = create_access_token(str(user.id), {"role": user.role})
    refresh = create_refresh_token(str(user.id))

    await log_action(
        db,
        actor_id=str(user.id),
        action="login_success",
        resource_type="auth",
        resource_id=data.username,
    )

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> TokenResponse:
    payload = decode_token(refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise UnauthorizedError("Invalid refresh token")

    # "sub" is always a string in the JWT; the id column is a native UUID.
    try:
        user_pk = uuid.UUID(payload["sub"])
    except (ValueError, AttributeError, TypeError, KeyError):
        raise UnauthorizedError("Invalid refresh token")

    user = await db.get(User, user_pk)
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found")

    access = create_access_token(str(user.id), {"role": user.role})
    new_refresh = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access,
        refresh_token=new_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )