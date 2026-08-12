import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
import cv2

from app.core import crypto
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.modules.auth.model import User
from app.modules.cameras.capture_manager import capture_manager
from app.modules.cameras.schemas import (
    CameraCreate,
    CameraDetail,
    CameraOut,
    CameraUpdate,
    DiscoveredDevice,
    TestConnectionRequest,
    TestConnectionResponse,
)
from app.modules.cameras.service import (
    create_camera,
    delete_camera,
    get_camera,
    list_cameras,
    test_connection,
    update_camera,
)

router = APIRouter()


# ── List / Create ──

@router.get("", response_model=list[CameraOut])
async def get_cameras(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await list_cameras(db)


@router.post("", response_model=CameraOut, status_code=201)
async def add_camera(
    body: CameraCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_camera(db, body, actor_id=str(current_user.id))


# ── Discovery ──

@router.get("/discover", response_model=list[DiscoveredDevice])
async def discover_devices(
    _: User = Depends(get_current_user),
):
    active_sources = capture_manager.get_active_sources()
    devices = await asyncio.to_thread(_scan_devices, active_sources)
    return devices


# ── Test Connection ──

@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_cam_connection(
    body: TestConnectionRequest,
    _: User = Depends(get_current_user),
):
    return await test_connection(body.rtsp_url)


# ── Stream (async generator — non-blocking!) ──

@router.get("/{camera_id}/stream")
async def stream_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    camera = await get_camera(db, camera_id)
    source = crypto.decrypt_str(camera.rtsp_url_encrypted)

    return StreamingResponse(
        _async_frames(source),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


async def _async_frames(source: str):
    """Async generator — reads from CaptureManager, never blocks event loop."""
    try:
        while True:
            jpeg = capture_manager.get_frame(source)
            if jpeg:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
                )
            await asyncio.sleep(0.033)  # ~30 fps
    except (asyncio.CancelledError, GeneratorExit):
        pass


# ── Single camera CRUD ──

@router.get("/{camera_id}", response_model=CameraDetail)
async def get_camera_detail(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await get_camera(db, camera_id)


@router.put("/{camera_id}", response_model=CameraOut)
async def edit_camera(
    camera_id: uuid.UUID,
    body: CameraUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_camera(db, camera_id, body, actor_id=str(current_user.id))


@router.delete("/{camera_id}", status_code=204)
async def remove_camera(
    camera_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_camera(db, camera_id, actor_id=str(current_user.id))


# ── Helpers ──

def _scan_devices(active_sources: set[str]) -> list[dict]:
    """Scan USB cameras — one per physical device (runs in thread pool).
    Skips devices that are already actively streaming to avoid stealing handles.
    """
    devices = []
    seen_frames = []

    # Build set of USB indices already streaming
    active_usb_indices = set()
    for src in active_sources:
        if src.startswith("usb://"):
            try:
                active_usb_indices.add(int(src.replace("usb://", "")))
            except ValueError:
                pass

    for i in range(5):
        # If this device is already streaming, report it without opening it
        if i in active_usb_indices:
            devices.append({
                "index": i,
                "name": f"Camera {i}",
                "resolution": "active",
                "working": True,
                "url": f"usb://{i}",
            })
            continue

        cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
        if not cap.isOpened():
            continue

        for _ in range(10):
            cap.read()

        ret, frame = cap.read()
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        if not ret or frame is None:
            continue

        brightness = float(frame.mean())
        if brightness <= 1.0:
            continue

        # Deduplicate: compare small thumbnail against already-seen frames
        thumb = cv2.resize(frame, (32, 32)).mean(axis=2)  # grayscale 32x32
        is_duplicate = False
        for prev in seen_frames:
            diff = abs(thumb.astype(float) - prev.astype(float)).mean()
            if diff < 5.0:
                is_duplicate = True
                break

        if is_duplicate:
            continue

        seen_frames.append(thumb)
        devices.append({
            "index": i,
            "name": f"Camera {i}",
            "resolution": f"{w}x{h}",
            "working": True,
            "url": f"usb://{i}",
        })

    return devices