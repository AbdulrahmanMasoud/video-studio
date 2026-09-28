"""API tests run inside the compose network against the real test Postgres, Redis, MinIO and Mailpit.

    docker compose run --rm -e DATABASE_URL=... api pytest        (see `make test-api`)
The schema is created with Alembic on the test database at session start and dropped at the end.
"""
from __future__ import annotations

import io
import os
import uuid

import httpx
import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text

from alembic import command

os.environ.setdefault("RATE_LIMITS_ENABLED", "0")
os.environ.setdefault("APP_ENV", "test")

from vs_api.config import get_settings  # noqa: E402

TEST_URL_SYNC = os.environ.get("DATABASE_URL_TEST_SYNC", get_settings().database_url_test_sync)
TEST_URL_ASYNC = TEST_URL_SYNC.replace("postgresql+psycopg://", "postgresql+asyncpg://")
os.environ["DATABASE_URL"] = TEST_URL_ASYNC
os.environ["DATABASE_URL_SYNC"] = TEST_URL_SYNC
get_settings.cache_clear()

from vs_api.core import db as dbmod  # noqa: E402

dbmod.async_engine.cache_clear(); dbmod.async_session_factory.cache_clear(); dbmod.sync_engine.cache_clear()
API_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session", autouse=True)
def schema():
    cfg = Config(os.path.join(API_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(API_DIR, "alembic"))
    cfg.set_main_option("sqlalchemy.url", TEST_URL_SYNC)
    eng = create_engine(TEST_URL_SYNC, isolation_level="AUTOCOMMIT")
    with eng.connect() as c:
        c.execute(text("drop schema public cascade; create schema public"))
    command.upgrade(cfg, "head")
    yield
    eng.dispose()


@pytest.fixture
async def client():
    from vs_api.main import app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


def unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:10]}@example.com"


async def register(client: httpx.AsyncClient, email: str | None = None, password: str = "correct-horse-battery", locale="en") -> dict:
    """Register and return {email, password, headers} using bearer auth (no CSRF needed)."""
    email = email or unique_email()
    r = await client.post("/auth/register", json={"email": email, "password": password, "locale": locale})
    assert r.status_code == 201, r.text
    data = r.json()
    return {"email": email, "password": password, "user": data["user"], "headers": {"Authorization": f"Bearer {data['access_token']}"}, "csrf": data["csrf_token"]}


ADMIN = {"X-Admin-Key": get_settings().admin_api_key}


async def mailpit_messages(to: str) -> list[dict]:
    host = os.environ.get("MAILPIT_HOST", "mailpit")
    async with httpx.AsyncClient(base_url=f"http://{host}:8025", timeout=10) as c:
        r = await c.get("/api/v1/search", params={"query": f"to:{to}"})
        return r.json().get("messages", []) if r.status_code == 200 else []


async def mailpit_body(msg_id: str) -> str:
    host = os.environ.get("MAILPIT_HOST", "mailpit")
    async with httpx.AsyncClient(base_url=f"http://{host}:8025", timeout=10) as c:
        r = await c.get(f"/api/v1/message/{msg_id}")
        return r.json().get("Text", "")


def png_bytes(size=(320, 320), color=(200, 30, 60)) -> bytes:
    from PIL import Image
    buf = io.BytesIO(); Image.new("RGB", size, color).save(buf, "PNG"); return buf.getvalue()


async def upload_presigned(post: dict, data: bytes, content_type: str) -> None:
    """Perform the browser's multipart POST to S3 (from inside the network the public endpoint is rewritten)."""
    url = post["url"].replace(get_settings().s3_public_endpoint_url, get_settings().s3_endpoint_url)
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(url, data=post["fields"], files={"file": ("f", data, content_type)})
        assert r.status_code in (200, 201, 204), r.text
