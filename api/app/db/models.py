"""
Central model registry — imports every module model so Alembic and
Base.metadata.create_all() discover them.
"""

from app.modules.auth.model import User  # noqa: F401
from app.modules.cameras.model import Camera, CameraZone  # noqa: F401
from app.modules.devices.model import Device  # noqa: F401
from app.modules.events.model import Event  # noqa: F401
from app.modules.recordings.model import Recording  # noqa: F401
from app.modules.settings.model import SystemSetting, AuditLog  # noqa: F401