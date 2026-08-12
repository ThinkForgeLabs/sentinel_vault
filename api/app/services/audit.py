"""
Convenience wrapper for audit logging used across modules.

log_action() writes into the caller's ambient session/transaction, so a
successful action and its audit row commit (or roll back) together as one
unit — the normal case for "X happened, log that X happened."

log_action_standalone() opens and commits its own short-lived session
instead. Use it for security-relevant events that must survive even when
the surrounding request is about to fail/rollback — the canonical
example being a failed login attempt: the auth service raises
UnauthorizedError right after logging it, and app/db/session.py's get_db()
rolls back the whole request session on any exception, which would
silently swallow an audit row written with the ambient session.
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


async def log_action_standalone(
    actor_id: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    details: dict | None = None,
) -> None:
    from app.db.session import async_session_factory

    async with async_session_factory() as session:
        await write_audit(
            session,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
        )
        await session.commit()