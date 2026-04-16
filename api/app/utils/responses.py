from typing import Any

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str
    data: Any | None = None


def ok(message: str = "Success", data: Any = None) -> dict:
    return {"message": message, "data": data}