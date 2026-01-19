from __future__ import annotations

from typing import Optional

import bcrypt
from fastapi import Request
from sqladmin.authentication import AuthenticationBackend

from app.core.config import admin_user


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        email = form.get("username")
        password = form.get("password")
        if not email or not password:
            return False
        if email != admin_user.email:
            return False
        if not bcrypt.checkpw(password.encode("utf-8"), admin_user.password_hash.encode("utf-8")):
            return False
        request.session.update({"user": email})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> Optional[bool]:
        return bool(request.session.get("user"))
