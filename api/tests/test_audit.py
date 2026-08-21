"""Verify audit logging is actually wired up end-to-end: real HTTP actions
against auth/cameras/settings/users must leave a matching AuditLog row,
and a failed login (whose request session gets rolled back) must still
produce a row via log_action_standalone."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.settings.model import AuditLog


async def _actions(db_session: AsyncSession) -> list[str]:
    result = await db_session.execute(select(AuditLog.action_type))
    return [row[0] for row in result.all()]


@pytest.mark.asyncio
async def test_login_success_is_audited(client: AsyncClient, admin_user, db_session):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "testadmin", "password": "testpass123"},
    )
    assert resp.status_code == 200
    assert "login_success" in await _actions(db_session)


@pytest.mark.asyncio
async def test_login_failure_is_audited_despite_rollback(
    client: AsyncClient, admin_user, db_session
):
    """The auth service logs the failed attempt via log_action_standalone
    (its own independently-committed session) specifically so this survives
    get_db()'s rollback-on-exception when UnauthorizedError is raised."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "testadmin", "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert "login_failed" in await _actions(db_session)


@pytest.mark.asyncio
async def test_create_camera_is_audited(client: AsyncClient, auth_headers, db_session):
    resp = await client.post(
        "/api/v1/cameras",
        json={"name": "Audited Cam", "rtsp_url": "rtsp://1.2.3.4/stream"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert "create_camera" in await _actions(db_session)


@pytest.mark.asyncio
async def test_update_and_delete_camera_are_audited(
    client: AsyncClient, auth_headers, db_session
):
    create_resp = await client.post(
        "/api/v1/cameras",
        json={"name": "Cam To Edit", "rtsp_url": "rtsp://1.2.3.4/stream"},
        headers=auth_headers,
    )
    camera_id = create_resp.json()["id"]

    update_resp = await client.put(
        f"/api/v1/cameras/{camera_id}",
        json={"name": "Cam Renamed"},
        headers=auth_headers,
    )
    assert update_resp.status_code == 200

    delete_resp = await client.delete(f"/api/v1/cameras/{camera_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    actions = await _actions(db_session)
    assert "update_camera" in actions
    assert "delete_camera" in actions

    # RTSP credentials must never leak into audit details.
    result = await db_session.execute(
        select(AuditLog.details_json).where(AuditLog.action_type == "update_camera")
    )
    for (details_json,) in result.all():
        assert "1.2.3.4" not in details_json


@pytest.mark.asyncio
async def test_write_setting_is_audited(client: AsyncClient, auth_headers, db_session):
    resp = await client.put(
        "/api/v1/settings/theme",
        json={"value_json": '"dark"'},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert "update_setting" in await _actions(db_session)


@pytest.mark.asyncio
async def test_create_and_delete_user_are_audited(client: AsyncClient, auth_headers, db_session):
    create_resp = await client.post(
        "/api/v1/users",
        json={
            "username": "audited_viewer",
            "display_name": "Audited Viewer",
            "password": "viewerpass123",
            "role": "viewer",
        },
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    user_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/v1/users/{user_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    actions = await _actions(db_session)
    assert "create_user" in actions
    assert "delete_user" in actions

    # Passwords must never leak into audit details.
    result = await db_session.execute(
        select(AuditLog.details_json).where(AuditLog.action_type == "create_user")
    )
    for (details_json,) in result.all():
        assert "viewerpass123" not in details_json
