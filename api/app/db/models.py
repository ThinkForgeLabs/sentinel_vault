"""
Central model registry — imports every module model so Alembic and
Base.metadata.create_all() discover them.
"""

from app.modules.auth.model import User  # noqa: F401
from app.modules.cameras.model import Camera, CameraZone  # noqa: F401
from app.modules.events.model import Event, Detection  # noqa: F401
from app.modules.settings.model import SystemSetting, AuditLog  # noqa: F401