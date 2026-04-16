import os
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("storage")


def ensure_storage_dirs() -> None:
    dirs = [settings.storage_root, settings.upload_root]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
        logger.info("Storage dir ready: %s", d)


def get_segment_path(camera_id: str, segment_name: str) -> Path:
    base = Path(settings.storage_root) / camera_id
    base.mkdir(parents=True, exist_ok=True)
    return base / segment_name


def get_clip_path(clip_id: str) -> Path:
    base = Path(settings.storage_root) / "clips"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{clip_id}.mp4"


def get_thumbnail_path(event_id: str) -> Path:
    base = Path(settings.storage_root) / "thumbnails"
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{event_id}.jpg"


def get_upload_path(filename: str) -> Path:
    base = Path(settings.upload_root)
    base.mkdir(parents=True, exist_ok=True)
    return base / filename


def get_storage_usage() -> dict:
    root = Path(settings.storage_root)
    if not root.exists():
        return {"used_bytes": 0, "file_count": 0}

    total_size = 0
    file_count = 0
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
            file_count += 1

    return {"used_bytes": total_size, "file_count": file_count}