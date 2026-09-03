from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.db.session import get_db
from app.dependencies.auth import get_current_user, require_owner
from app.modules.auth.model import User
from app.modules.ml_models import service
from app.modules.ml_models.schemas import MLModelOut

router = APIRouter()

MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB


@router.get("", response_model=list[MLModelOut])
async def list_models(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await service.list_models(db)


@router.post("", response_model=MLModelOut, status_code=201)
async def upload_model(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_owner),
):
    data = await file.read()
    if len(data) > MAX_UPLOAD_SIZE:
        raise BadRequestError("Model file too large (max 500 MB)")
    return await service.save_uploaded_model(db, file.filename, data)


@router.put("/{model_id}/default", response_model=MLModelOut)
async def set_default_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_owner),
):
    return await service.set_default_model(db, model_id)


@router.delete("/{model_id}", status_code=204)
async def delete_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_owner),
):
    await service.delete_model(db, model_id)
