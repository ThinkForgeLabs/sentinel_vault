"""Regression coverage for app.db.base.GUID.

Before GUID existed, UUIDMixin used sqlalchemy.dialects.postgresql.UUID
directly. On SQLite that column gets NUMERIC type affinity, and a UUID whose
hex digits are all 0-9 (e.g. the fixed "00000000-0000-0000-0000-000000000001"
id used by the demo seed script) would silently round-trip as the integer 1
instead of the intended UUID, corrupting the primary key and breaking lookups
for that row. GUID forces a CHAR(36)/TEXT-affinity column on non-PostgreSQL
backends so the value always survives as the literal UUID string.
"""

import sqlite3
import uuid

import pytest

from app.core.security import hash_password
from app.modules.auth.model import User

ALL_DIGIT_UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")


@pytest.mark.asyncio
async def test_all_digit_uuid_round_trips_through_orm(db_session):
    user = User(
        id=ALL_DIGIT_UUID,
        username="digituser",
        display_name="Digit User",
        password_hash=hash_password("x"),
        role="owner",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    fetched = await db_session.get(User, ALL_DIGIT_UUID)
    assert fetched is not None
    assert fetched.id == ALL_DIGIT_UUID
    assert isinstance(fetched.id, uuid.UUID)


@pytest.mark.asyncio
async def test_all_digit_uuid_stored_as_text_on_disk(db_session):
    user = User(
        id=ALL_DIGIT_UUID,
        username="digituser2",
        display_name="Digit User 2",
        password_hash=hash_password("x"),
        role="owner",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    conn = sqlite3.connect("./test.db")
    try:
        row = conn.execute(
            "select typeof(id), id from users where username = ?", ("digituser2",)
        ).fetchone()
    finally:
        conn.close()

    assert row is not None
    column_type, raw_value = row
    assert column_type == "text"
    assert raw_value == str(ALL_DIGIT_UUID)
