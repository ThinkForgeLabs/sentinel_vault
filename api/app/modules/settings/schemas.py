from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SettingOut(BaseModel):
    key: str
    value_json: str
    updated_at: datetime

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    value_json: str


class BulkSettingsUpdate(BaseModel):
    settings: dict[str, str]


class SetupInitRequest(BaseModel):
    storage_path: str = "./data/recordings"
    admin_username: str = Field(default="admin", min_length=2, max_length=100)
    admin_display_name: str = Field(default="Administrator", min_length=1, max_length=200)
    admin_password: str = Field(..., min_length=8)
    encryption_enabled: bool = True


class SetupStateResponse(BaseModel):
    complete: bool
    step: str


class SetupUserOut(BaseModel):
    id: UUID
    username: str
    display_name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SetupCompleteResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: SetupUserOut