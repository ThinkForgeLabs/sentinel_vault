import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.db.session import get_db
from app.modules.auth.model import User

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload is None or payload.get("type") != "access":
        raise UnauthorizedError("Invalid or expired token")

    user_id = payload.get("sub")
    if user_id is None:
        raise UnauthorizedError("Invalid token payload")

    # JWT "sub" is always a string per spec, but the id column is a native
    # UUID type -- convert before querying so the driver's UUID bind
    # processor (which expects a uuid.UUID, not a str) doesn't blow up.
    try:
        user_pk = uuid.UUID(user_id)
    except (ValueError, AttributeError, TypeError):
        raise UnauthorizedError("Invalid token payload")

    user = await db.get(User, user_pk)
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    return user


async def require_owner(user: User = Depends(get_current_user)) -> User:
    if user.role != "owner":
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError("Owner access required")
    return user