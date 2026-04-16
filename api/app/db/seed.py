"""
Seed script for demo / dev data.
Run with: python -m app.db.seed
"""

import asyncio
import uuid

from app.core.security import hash_password
from app.db.session import async_session_factory
from app.modules.auth.model import User
from app.modules.cameras.model import Camera
from app.modules.settings.model import SystemSetting
from app.core.logging import get_logger

logger = get_logger("seed")


async def seed() -> None:
    async with async_session_factory() as session:
        # ── Admin user ──
        existing = await session.get(User, uuid.UUID("00000000-0000-0000-0000-000000000001"))
        if existing is None:
            admin = User(
                id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
                username="admin",
                display_name="Admin",
                password_hash=hash_password("sentinel"),
                role="owner",
                is_active=True,
            )
            session.add(admin)
            logger.info("Created admin user (admin / sentinel)")

        # ── Demo cameras ──
        demo_cameras = [
            {"name": "Front Door", "location_label": "Main Entrance", "rtsp_url": "rtsp://192.168.1.10:554/stream1"},
            {"name": "Backyard", "location_label": "Garden", "rtsp_url": "rtsp://192.168.1.11:554/stream1"},
            {"name": "Garage", "location_label": "Driveway", "rtsp_url": "rtsp://192.168.1.12:554/stream1"},
        ]
        for cam_data in demo_cameras:
            cam = Camera(
                name=cam_data["name"],
                location_label=cam_data["location_label"],
                rtsp_url_encrypted=cam_data["rtsp_url"],
                status="offline",
                record_enabled=True,
                ai_enabled=True,
                retention_days=14,
            )
            session.add(cam)

        # ── Default settings ──
        defaults = {
            "setup_complete": "false",
            "theme": "dark",
            "timezone": "UTC",
        }
        for key, value in defaults.items():
            setting = SystemSetting(key=key, value_json=f'"{value}"')
            session.add(setting)

        await session.commit()
        logger.info("Seed complete.")


if __name__ == "__main__":
    asyncio.run(seed())