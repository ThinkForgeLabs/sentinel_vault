"""
Bootstrap the first admin ("owner") account for a fresh deployment.

Unlike app/db/seed.py (which is dev/demo data -- a hardcoded admin/sentinel
account plus fake demo cameras), this creates ONLY a single owner-role user
with a username/password you choose. It's safe to run against a real
production database.

Usage (inside the api container):

    docker compose -f docker-compose.prod.yml exec api python -m app.db.create_admin

    # or non-interactively:
    docker compose -f docker-compose.prod.yml exec api \\
        python -m app.db.create_admin --username admin --password 'a-real-password'

Refuses to create a duplicate if the username already exists.
"""

import argparse
import asyncio
import getpass
import sys
import uuid

from sqlalchemy import select

from app.core.logging import get_logger
from app.core.security import hash_password
from app.db.session import async_session_factory
from app.modules.auth.model import User

logger = get_logger("create_admin")


async def create_admin(username: str, password: str, display_name: str | None = None) -> None:
    async with async_session_factory() as session:
        existing = await session.scalar(select(User).where(User.username == username))
        if existing is not None:
            print(f"User '{username}' already exists -- not creating a duplicate.")
            return

        user = User(
            id=uuid.uuid4(),
            username=username,
            display_name=display_name or username.capitalize(),
            password_hash=hash_password(password),
            role="owner",
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"Created owner account '{username}'.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create the first admin (owner) account.")
    parser.add_argument("--username", default="admin")
    parser.add_argument(
        "--password",
        default=None,
        help="If omitted, you'll be prompted securely (input is hidden).",
    )
    parser.add_argument("--display-name", default=None)
    args = parser.parse_args()

    password = args.password
    if not password:
        password = getpass.getpass(f"Password for '{args.username}': ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords did not match.", file=sys.stderr)
            sys.exit(1)

    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        sys.exit(1)

    asyncio.run(create_admin(args.username, password, args.display_name))


if __name__ == "__main__":
    main()
