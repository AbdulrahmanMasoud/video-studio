"""Rate limits: slowapi (per IP) for auth endpoints, a small Redis fixed window for per-user limits."""
from __future__ import annotations

from fastapi import HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import get_settings
from .core import queue as q


def _key(request: Request) -> str:
    return request.headers.get("X-Forwarded-For", "").split(",")[0].strip() or get_remote_address(request)


limiter = Limiter(key_func=_key, storage_uri=get_settings().redis_url, enabled=get_settings().rate_limits_enabled, headers_enabled=True)


def check_user_limit(user_id, bucket: str, limit: int, window_s: int = 3600) -> None:
    """Raise 429 when the user exceeded `limit` events in the current fixed window."""
    if not get_settings().rate_limits_enabled:
        return
    r = q.conn()
    key = f"rl:{bucket}:{user_id}"
    n = r.incr(key)
    if n == 1:
        r.expire(key, window_s)
    if n > limit:
        raise HTTPException(429, detail={"error_code": "rate_limited", "message": f"limit of {limit} per {window_s // 60} min reached"})
