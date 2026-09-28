"""FastAPI dependencies: db session, current user (cookie or bearer), CSRF for cookie sessions, admin key."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .core.db import get_session
from .core.models import User
from .core.security import read_token

ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE = "vs_access", "vs_refresh", "vs_csrf"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

DB = Annotated[AsyncSession, Depends(get_session)]


def err(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status, detail={"error_code": code, "message": message})


async def _user_from_request(request: Request, db: AsyncSession) -> User | None:
    token, via_cookie = None, False
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:].strip()
    elif request.cookies.get(ACCESS_COOKIE):
        token, via_cookie = request.cookies[ACCESS_COOKIE], True
    if not token:
        return None
    data = read_token(token, "access")
    if not data:
        return None
    if via_cookie and request.method not in SAFE_METHODS:
        # CSRF double submit: the non-httpOnly cookie must match the header
        if not request.cookies.get(CSRF_COOKIE) or request.headers.get("X-CSRF-Token") != request.cookies.get(CSRF_COOKIE):
            raise err(403, "csrf", "missing or invalid CSRF token")
    try:
        uid = uuid.UUID(data["sub"])
    except (KeyError, ValueError):
        return None
    user = (await db.execute(select(User).where(User.id == uid, User.deleted_at.is_(None)))).scalar_one_or_none()
    return user


async def current_user(request: Request, db: DB) -> User:
    user = await _user_from_request(request, db)
    if not user:
        raise err(401, "unauthenticated", "sign in required")
    return user


async def optional_user(request: Request, db: DB) -> User | None:
    return await _user_from_request(request, db)


async def verified_user(user: Annotated[User, Depends(current_user)]) -> User:
    if get_settings().is_prod and not user.email_verified_at:
        raise err(403, "email_unverified", "verify your email first")
    return user


CurrentUser = Annotated[User, Depends(current_user)]
VerifiedUser = Annotated[User, Depends(verified_user)]


def require_admin(x_admin_key: Annotated[str | None, Header()] = None) -> None:
    s = get_settings()
    if not x_admin_key or x_admin_key != s.admin_api_key:
        raise err(401, "admin_key", "invalid admin key")


Admin = Annotated[None, Depends(require_admin)]
