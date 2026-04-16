"""
Convenience wrapper for audit logging used across modules.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.service import write_audit


async def log_action(
    db: AsyncSession,
    actor_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict | None = None,
) -> None:
    await write_audit(
        db,
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )