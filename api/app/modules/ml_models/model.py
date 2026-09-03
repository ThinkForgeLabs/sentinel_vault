from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class MLModel(UUIDMixin, TimestampMixin, Base):
    """A detection model file available to run on a camera.

    Both the bundled stock model (source="stock") and any number of
    user-uploaded custom models (source="custom") live in this same table,
    so a camera's model_id FK works identically either way.
    """

    __tablename__ = "ml_models"

    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    format: Mapped[str] = mapped_column(String(20), nullable=False, default="pt")
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="custom")
    class_names_json: Mapped[str] = mapped_column(Text, default="[]")
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
