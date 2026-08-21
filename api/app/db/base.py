import uuid
from datetime import datetime, timezone

from sqlalchemy import CHAR, DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    pass


class GUID(TypeDecorator):
    """Platform-independent UUID column type.

    Uses PostgreSQL's native UUID type when available, otherwise stores as a
    CHAR(36) string. This avoids a subtle SQLite bug: with a plain UUID column
    (declared type "UUID", which SQLite gives NUMERIC affinity), a UUID whose
    hex digits happen to be all 0-9 (no a-f) round-trips through SQLite's
    NUMERIC affinity as an integer instead of the intended UUID string,
    corrupting the primary key. Declaring the SQLite fallback as CHAR(36)
    forces TEXT affinity, so the value is always stored and read back as the
    literal UUID string, regardless of its digits. PostgreSQL deployments are
    unaffected — this compiles to the same native UUID column as before.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return value
        if not isinstance(value, uuid.UUID):
            value = uuid.UUID(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class UUIDMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )