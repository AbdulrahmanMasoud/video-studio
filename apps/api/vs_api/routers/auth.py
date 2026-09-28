"""Email + password auth with argon2, JWT access/refresh cookies, CSRF double-submit, email verification and password reset."""
from __future__ import annotations

import hashlib
from datetime import datetime

from fastapi import APIRouter, Request, Response
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from ..config import get_settings
from ..core import email as mailer
from ..core.models import User
from ..core.security import access_token, csrf_token, email_token, hash_password, read_token, refresh_token, verify_password
from ..deps import ACCESS_COOKIE, CSRF_COOKIE, DB, REFRESH_COOKIE, CurrentUser, err
from ..ratelimit import limiter
from ..schemas import AuthOut, ForgotIn, LoginIn, Msg, RegisterIn, ResetIn, TokenIn, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


def user_out(u: User) -> UserOut:
    return UserOut(id=u.id, email=u.email, locale=u.locale, plan=u.plan, credits=u.credits, email_verified=bool(u.email_verified_at), is_admin=u.is_admin,
                   created_at=u.created_at)


def set_session_cookies(response: Response, user: User) -> AuthOut:
    s = get_settings()
    acc, ref, csrf = access_token(user.id), refresh_token(user.id), csrf_token()
    response.set_cookie(ACCESS_COOKIE, acc, max_age=s.access_token_ttl_s, httponly=True, secure=s.cookie_secure, samesite="lax", path="/")
    response.set_cookie(REFRESH_COOKIE, ref, max_age=s.refresh_token_ttl_s, httponly=True, secure=s.cookie_secure, samesite="lax", path="/auth")
    response.set_cookie(CSRF_COOKIE, csrf, max_age=s.refresh_token_ttl_s, httponly=False, secure=s.cookie_secure, samesite="lax", path="/")
    return AuthOut(user=user_out(user), csrf_token=csrf, access_token=acc)


def clear_session_cookies(response: Response) -> None:
    for name, path in ((ACCESS_COOKIE, "/"), (REFRESH_COOKIE, "/auth"), (CSRF_COOKIE, "/")):
        response.delete_cookie(name, path=path)


async def send_verification(user: User) -> None:
    s = get_settings()
    link = f"{s.web_origin}/verify?token={email_token(user.id, 'verify', user.email)}"
    await run_in_threadpool(mailer.send, user.email, "verify", user.locale, link=link)


@router.post("/register", response_model=AuthOut, status_code=201)
@limiter.limit("10/minute")
async def register(request: Request, response: Response, body: RegisterIn, db: DB):
    email = body.email.lower()
    if (await db.execute(select(User.id).where(User.email == email))).first():
        raise err(409, "email_taken", "an account with this email already exists")
    user = User(email=email, password_hash=hash_password(body.password), locale=body.locale, plan="free", credits=0)
    db.add(user)
    await db.flush()
    from ..core import credits as cr
    from ..core.plans import plan
    await db.run_sync(lambda s: cr.grant(s, user.id, int(plan("free")["credits"]), "grant", external_id=f"signup:{user.id}", note="free plan signup credits"))
    await db.commit()
    await db.refresh(user)
    await send_verification(user)
    return set_session_cookies(response, user)


@router.post("/login", response_model=AuthOut)
@limiter.limit("10/minute")
async def login(request: Request, response: Response, body: LoginIn, db: DB):
    user = (await db.execute(select(User).where(User.email == body.email.lower(), User.deleted_at.is_(None)))).scalar_one_or_none()
    if not user or not verify_password(body.password, user.password_hash):
        raise err(401, "bad_credentials", "wrong email or password")
    return set_session_cookies(response, user)


@router.post("/logout", response_model=Msg)
async def logout(response: Response):
    clear_session_cookies(response)
    return Msg(message="signed out")


@router.post("/refresh", response_model=AuthOut)
@limiter.limit("30/minute")
async def refresh(request: Request, response: Response, db: DB):
    tok = request.cookies.get(REFRESH_COOKIE) or (request.headers.get("Authorization", "")[7:] if request.headers.get("Authorization", "").startswith("Bearer ") else None)
    data = read_token(tok, "refresh") if tok else None
    if not data:
        clear_session_cookies(response)
        raise err(401, "refresh_invalid", "sign in again")
    user = (await db.execute(select(User).where(User.id == data["sub"], User.deleted_at.is_(None)))).scalar_one_or_none()
    if not user:
        raise err(401, "refresh_invalid", "sign in again")
    return set_session_cookies(response, user)


@router.post("/verify", response_model=Msg)
@limiter.limit("10/minute")
async def verify(request: Request, body: TokenIn, db: DB):
    data = read_token(body.token, "verify")
    user = (await db.execute(select(User).where(User.id == data["sub"]))).scalar_one_or_none() if data else None
    if not user:
        raise err(400, "token_invalid", "this verification link is invalid or expired")
    if not user.email_verified_at:
        user.email_verified_at = datetime.utcnow()
        await db.commit()
    return Msg(message="email verified")


@router.post("/resend-verification", response_model=Msg)
@limiter.limit("3/minute")
async def resend_verification(request: Request, user: CurrentUser):
    if user.email_verified_at:
        return Msg(message="already verified")
    await send_verification(user)
    return Msg(message="verification email sent")


@router.post("/forgot", response_model=Msg)
@limiter.limit("5/minute")
async def forgot(request: Request, body: ForgotIn, db: DB):
    user = (await db.execute(select(User).where(User.email == body.email.lower(), User.deleted_at.is_(None)))).scalar_one_or_none()
    if user:
        s = get_settings()
        link = f"{s.web_origin}/reset?token={email_token(user.id, 'reset', user.password_hash[-16:])}"
        await run_in_threadpool(mailer.send, user.email, "reset", user.locale, link=link)
    return Msg(message="if the address exists, a reset email was sent")


@router.post("/reset", response_model=Msg)
@limiter.limit("10/minute")
async def reset(request: Request, response: Response, body: ResetIn, db: DB):
    data = read_token(body.token, "reset") or {}
    user = (await db.execute(select(User).where(User.id == data["sub"]))).scalar_one_or_none() if data else None
    # the fingerprint binds the token to the password hash at issue time: single use
    if not user or data.get("fp") != hashlib.sha256(user.password_hash[-16:].lower().encode()).hexdigest()[:16]:
        raise err(400, "token_invalid", "this reset link is invalid or expired")
    user.password_hash = hash_password(body.password)
    await db.commit()
    clear_session_cookies(response)
    return Msg(message="password updated, sign in again")
