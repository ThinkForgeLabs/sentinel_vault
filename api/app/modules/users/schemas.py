import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    password: str = Field(..., min_length=8)
    role: str = Field(default="viewer")


class UserUpdate(BaseModel):
    display_name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class SelfUpdate(BaseModel):
    """Fields a user may change about their own account. Changing the
    password requires proving the current one — unlike UserUpdate, which
    is owner-gated and never sees a password field at all."""

    display_name: str | None = Field(None, min_length=1, max_length=200)
    current_password: str | None = None
    new_password: str | None = Field(None, min_length=8)


class UserOut(BaseModel):
    id: uuid.UUID
    username: str
    display_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}