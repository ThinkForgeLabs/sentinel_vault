# api/app/modules/auth/dependencies.py
"""
Stub auth dependency returns a fake user so routes work during development.
Replace with real JWT / session logic when auth is implemented.
"""

from fastapi import Request


async def get_current_user(request: Request) -> dict:
    return {
        "id": "dev-user",
        "username": "admin",
        "role": "admin",
    }