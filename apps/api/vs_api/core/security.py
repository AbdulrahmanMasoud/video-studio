"""Password hashing (argon2), JWT access/refresh tokens, signed single-use email tokens, CSRF tokens."""
from __future__ import annotations

import hashlib
import secrets
import time
import uuid

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from ..config import get_settings

_ph = PasswordHasher()
ALG = "HS256"


def hash_password(pw: str) -> str:
    return _ph.hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, pw)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def _encode(payload: dict, ttl: int) -> str:
    now = int(time.time())
    return jwt.encode({**payload, "iat": now, "exp": now + ttl, "jti": uuid.uuid4().hex}, get_settings().secret_key, algorithm=ALG)


def _decode(token: str, kind: str) -> dict | None:
    try:
        data = jwt.decode(token, get_settings().secret_key, algorithms=[ALG])
    except jwt.PyJWTError:
        return None
    return data if data.get("kind") == kind else None


def access_token(user_id) -> str:
    return _encode({"sub": str(user_id), "kind": "access"}, get_settings().access_token_ttl_s)


def refresh_token(user_id) -> str:
    return _encode({"sub": str(user_id), "kind": "refresh"}, get_settings().refresh_token_ttl_s)


def email_token(user_id, purpose: str, email: str) -> str:
    """Single use: the payload carries a fingerprint of the current state (email + purpose) checked on use."""
    return _encode({"sub": str(user_id), "kind": purpose, "fp": hashlib.sha256(email.lower().encode()).hexdigest()[:16]}, get_settings().email_token_ttl_s)


def read_token(token: str, kind: str) -> dict | None:
    return _decode(token, kind)


def csrf_token() -> str:
    return secrets.token_urlsafe(32)
