"""
Model registry service — upload/list/delete/default-select management for
detection model files (both the bundled stock model and user-uploaded
custom models live in the same `ml_models` table).

Adapted from ThinkForgeLabs/ODDS (odds-v3) detection/service.py's model
management functions to Sentinel Vault's async SQLAlchemy + Postgres
stack (ODDS v3 used aiosqlite; the SQLAlchemy async API is identical).
"""

import json
import logging
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.detection.model_pool import model_pool
from app.modules.ml_models.model import MLModel
from app.modules.ml_models.schemas import MLModelOut

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".pt", ".onnx", ".engine", ".tflite"}


def _models_dir() -> Path:
    d = Path(settings.models_dir)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _to_out(model: MLModel) -> MLModelOut:
    try:
        class_names = json.loads(model.class_names_json)
    except (json.JSONDecodeError, TypeError):
        class_names = []
    return MLModelOut(
        id=model.id,
        filename=model.filename,
        format=model.format,
        source=model.source,
        is_default=model.is_default,
        size_bytes=model.size_bytes,
        size_mb=round(model.size_bytes / (1024 * 1024), 1),
        class_names=class_names,
        created_at=model.created_at,
    )


async def list_models(db: AsyncSession) -> list[MLModelOut]:
    result = await db.execute(select(MLModel).order_by(MLModel.created_at))
    return [_to_out(m) for m in result.scalars().all()]


async def get_model(db: AsyncSession, model_id: UUID) -> MLModel:
    model = await db.get(MLModel, model_id)
    if model is None:
        raise NotFoundError("MLModel", model_id)
    return model


async def get_default_model(db: AsyncSession) -> Optional[MLModel]:
    result = await db.execute(select(MLModel).where(MLModel.is_default.is_(True)).limit(1))
    model = result.scalar_one_or_none()
    if model is None:
        result = await db.execute(select(MLModel).limit(1))
        model = result.scalar_one_or_none()
    return model


async def save_uploaded_model(
    db: AsyncSession, filename: str, data: bytes, class_names: list[str] | None = None
) -> MLModelOut:
    """Save an uploaded custom model file to disk and register it in the DB."""
    safe_name = Path(filename).name
    if not safe_name:
        raise BadRequestError("Invalid filename")

    ext = Path(safe_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BadRequestError(
            f"Unsupported format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    dest = _models_dir() / safe_name
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    try:
        tmp.write_bytes(data)
        tmp.rename(dest)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise

    model = MLModel(
        filename=safe_name,
        file_path=str(dest),
        format=ext.lstrip("."),
        source="custom",
        class_names_json=json.dumps(class_names or []),
        is_default=False,
        size_bytes=dest.stat().st_size,
    )
    db.add(model)
    await db.flush()
    logger.info("Custom model saved: %s (%d bytes)", dest, model.size_bytes)
    return _to_out(model)


async def register_stock_model(
    db: AsyncSession, file_path: str, class_names: list[str], make_default: bool = True
) -> MLModelOut:
    """Register the bundled stock model on first startup, if not already present."""
    existing = await db.execute(select(MLModel).where(MLModel.source == "stock"))
    found = existing.scalar_one_or_none()
    if found:
        return _to_out(found)

    p = Path(file_path)
    size = p.stat().st_size if p.exists() else 0

    model = MLModel(
        filename=p.name,
        file_path=str(p),
        format=p.suffix.lstrip(".") or "pt",
        source="stock",
        class_names_json=json.dumps(class_names),
        is_default=make_default,
        size_bytes=size,
    )
    db.add(model)
    await db.flush()
    logger.info("Stock model registered: %s", p)
    return _to_out(model)


async def delete_model(db: AsyncSession, model_id: UUID) -> None:
    model = await get_model(db, model_id)
    if model.source == "stock":
        raise BadRequestError("Cannot delete the bundled stock model")

    if model_pool.is_loaded(model.file_path):
        model_pool.unload(model.file_path)

    p = Path(model.file_path)
    if p.exists():
        p.unlink()

    await db.delete(model)
    await db.flush()
    logger.info("Model deleted: %s", model.file_path)


async def set_default_model(db: AsyncSession, model_id: UUID) -> MLModelOut:
    target = await get_model(db, model_id)

    result = await db.execute(select(MLModel).where(MLModel.is_default.is_(True)))
    for m in result.scalars().all():
        m.is_default = False

    target.is_default = True
    await db.flush()
    return _to_out(target)
