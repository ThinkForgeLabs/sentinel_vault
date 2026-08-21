"""
Helpers for serving encrypted recordings/clips/thumbnails to the browser.

Every recording segment, motion clip, and thumbnail is encrypted at rest
(see app/core/crypto.py). That means every place that used to hand a file
path straight to FileResponse or ffmpeg now needs to decrypt into a
short-lived temp file first, serve/transcode from that, and clean the
temp file up once the response has actually been sent — the permanent
copy on disk stays ciphertext at all times.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Callable

from starlette.background import BackgroundTask

from app.core import crypto


def cleanup_task(path: Path) -> BackgroundTask:
    """BackgroundTask that deletes a temp file after the response is sent."""
    return BackgroundTask(lambda: path.unlink(missing_ok=True))


def decrypt_to_temp(path: Path, suffix: str = "") -> Path:
    """Decrypt `path` into a new temp file and return its Path. Caller is
    responsible for deleting it (typically via cleanup_task on the
    response)."""
    data = path.read_bytes()
    plaintext = crypto.decrypt_bytes(data)
    fd, tmp_name = tempfile.mkstemp(suffix=suffix)
    with os.fdopen(fd, "wb") as f:
        f.write(plaintext)
    return Path(tmp_name)


async def ensure_playable_encrypted(
    src_path: Path,
    cache_path: Path,
    transcode_fn: Callable[[str, str], None],
) -> Path:
    """
    Return a Path to a temp, decrypted, browser-playable (H.264/MP4) copy
    of the video at src_path, transcoding once and caching the result —
    encrypted — at cache_path for next time.

    transcode_fn(src_plain_path, dest_plain_path) does the actual ffmpeg
    call and must be a blocking/sync function; it's run in a thread.

    The caller must delete the returned temp path once the response has
    been sent (see cleanup_task).
    """
    if not (cache_path.exists() and cache_path.stat().st_size > 0):
        with crypto.decrypted_temp_copy(src_path, suffix=src_path.suffix) as plain_src:
            fd, tmp_out_name = tempfile.mkstemp(suffix=".mp4")
            os.close(fd)
            tmp_out = Path(tmp_out_name)
            try:
                await asyncio.to_thread(transcode_fn, str(plain_src), str(tmp_out))
                crypto.encrypt_file_in_place(tmp_out, cache_path)
            finally:
                tmp_out.unlink(missing_ok=True)

    return decrypt_to_temp(cache_path, suffix=".mp4")
