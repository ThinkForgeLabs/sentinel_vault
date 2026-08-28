import uuid
from datetime import datetime

from pydantic import BaseModel


class MLModelOut(BaseModel):
    id: uuid.UUID
    filename: str
    format: str
    source: str
    is_default: bool
    size_bytes: int
    size_mb: float
    class_names: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": False}
