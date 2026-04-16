from datetime import datetime

from pydantic import BaseModel


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
    admin_username: str = "admin"
    admin_password: str
    encryption_enabled: bool = True


class SetupStateResponse(BaseModel):
    complete: bool
    step: str