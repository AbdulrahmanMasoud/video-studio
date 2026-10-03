"""Lemon Squeezy webhooks with recorded payloads: signature check, idempotency, credit and plan effects. Also credit reservation
under concurrent renders and plan gating (free → 720p + watermark, paid → neither)."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import threading
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from vs_api.config import get_settings
from vs_api.core import credits, plans
from vs_api.core.db import sync_session_factory
from vs_api.core.models import Project, Subscription, User, WebhookEvent

from .conftest import ADMIN, register

FIX = Path(__file__).parent / "fixtures" / "lemonsqueezy"
SECRET = "test-webhook-secret"


@pytest.fixture(autouse=True)
def ls_env(monkeypatch):
    monkeypatch.setenv("LEMONSQUEEZY_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("LEMONSQUEEZY_VARIANT_STARTER", "100001")
    monkeypatch.setenv("LEMONSQUEEZY_VARIANT_PRO", "100002")
    monkeypatch.setenv("LEMONSQUEEZY_VARIANT_AGENCY", "100003")
    monkeypatch.setattr(get_settings(), "payments_provider", "lemonsqueezy")
    yield
    monkeypatch.setattr(get_settings(), "payments_provider", "mock")


def payload(name: str, user_id: str, email: str, ids: dict[str, str] | None = None) -> bytes:
    """Recorded payload with the user substituted; subscription/invoice/order ids are made unique per test (they are globally unique at LS)."""
    raw = (FIX / name).read_text().replace("{USER_ID}", user_id).replace("{EMAIL}", email)
    ids = ids or {}
    for old, new in (("123456", ids.get("sub", "123456")), ("55501", ids.get("inv", "55501")), ("55502", ids.get("inv2", "55502")), ("777", ids.get("order", "777")),
                     ("9001", ids.get("cust", "9001"))):
        raw = raw.replace(f'"{old}"', f'"{new}"').replace(f": {old},", f": {new},")
    return raw.encode()


def fresh_ids() -> dict[str, str]:
    n = int(uuid.uuid4().int % 10_000_000)
    return {"sub": str(900_000 + n), "inv": str(5_000_000 + n), "inv2": str(6_000_000 + n), "order": str(7_000_000 + n), "cust": str(80_000_000 + n)}


def sign(body: bytes, secret: str = SECRET) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


async def post(client, body: bytes, sig: str | None = None):
    headers = {"Content-Type": "application/json", "X-Event-Name": json.loads(body)["meta"]["event_name"]}
    if sig is not None:
        headers["X-Signature"] = sig
    return await client.post("/billing/webhooks/lemonsqueezy", content=body, headers=headers)


async def test_webhook_rejects_bad_signature(client):
    u = await register(client)
    body = payload("subscription_created.json", u["user"]["id"], u["email"])
    assert (await post(client, body)).status_code == 401
    assert (await post(client, body, "deadbeef")).status_code == 401
    assert (await post(client, body, sign(body, "other-secret"))).status_code == 401


async def test_subscription_lifecycle_credits_and_idempotency(client):
    u = await register(client)
    uid, email = u["user"]["id"], u["email"]
    ids = fresh_ids()
    me = lambda: client.get("/me", headers=u["headers"])  # noqa: E731
    assert (await me()).json()["user"]["credits"] == 2
    # created → plan pro, customer id stored; credits arrive with the first payment_success
    r = await post(client, body := payload("subscription_created.json", uid, email, ids), sign(body))
    assert r.status_code == 200 and r.json() == {"ok": True, "result": "applied", "event": "subscription_created"}
    m = (await me()).json()
    assert m["user"]["plan"] == "pro" and m["plan"]["watermark"] is False and m["plan"]["max_res"] == 2160
    r = await post(client, body := payload("subscription_payment_success.json", uid, email, ids), sign(body))
    assert r.json()["result"] == "applied"
    assert (await me()).json()["user"]["credits"] == 50
    # the same invoice delivered again changes nothing
    r = await post(client, body, sign(body))
    assert r.json()["result"] == "duplicate" and (await me()).json()["user"]["credits"] == 50
    with sync_session_factory()() as s:
        assert credits.balance(s, uuid.UUID(uid)) == 50
        user = s.get(User, uuid.UUID(uid)); assert user.ls_customer_id == ids["cust"]
        sub = s.execute(select(Subscription).where(Subscription.user_id == user.id)).scalar_one()
        assert sub.external_id == ids["sub"] and sub.status == "active" and sub.plan == "pro" and sub.raw["urls"]["customer_portal"].startswith("https://")
        assert s.execute(select(WebhookEvent).where(WebhookEvent.provider == "lemonsqueezy")).scalars().all()
    # subscription status endpoint + portal link from the stored subscription
    r = await client.get("/billing/subscription", headers=u["headers"])
    assert r.status_code == 200 and r.json()["status"] == "active" and r.json()["subscription_plan"] == "pro" and r.json()["current_period_end"]
    # updated → variant agency (plan change through the portal)
    r = await post(client, body := payload("subscription_updated.json", uid, email, ids), sign(body))
    assert r.json()["result"] == "applied" and (await me()).json()["user"]["plan"] == "agency"
    # cancelled → still paid until period end, flag set
    r = await post(client, body := payload("subscription_cancelled.json", uid, email, ids), sign(body))
    assert r.json()["result"] == "applied"
    sub_out = (await client.get("/billing/subscription", headers=u["headers"])).json()
    assert sub_out["cancel_at_period_end"] is True and (await me()).json()["user"]["plan"] == "agency"
    # payment failed → email only, plan unchanged, credits unchanged
    r = await post(client, body := payload("subscription_payment_failed.json", uid, email, ids), sign(body))
    assert r.json()["result"] == "applied" and (await me()).json()["user"]["credits"] == 50
    # expired → free plan, credits reset to the free allowance
    r = await post(client, body := payload("subscription_expired.json", uid, email, ids), sign(body))
    assert r.json()["result"] == "applied"
    m = (await me()).json()
    assert m["user"]["plan"] == "free" and m["user"]["credits"] == 2 and m["plan"]["watermark"] is True


async def test_order_refunded_removes_credits_and_downgrades(client):
    u = await register(client)
    uid, email = u["user"]["id"], u["email"]
    ids = fresh_ids()
    await post(client, body := payload("subscription_created.json", uid, email, ids), sign(body))
    await post(client, body := payload("subscription_payment_success.json", uid, email, ids), sign(body))
    assert (await client.get("/me", headers=u["headers"])).json()["user"]["credits"] == 50
    r = await post(client, body := payload("order_refunded.json", uid, email, ids), sign(body))
    assert r.json()["result"] == "applied"
    m = (await client.get("/me", headers=u["headers"])).json()
    assert m["user"]["plan"] == "free" and m["user"]["credits"] == 0
    # idempotent
    assert (await post(client, body, sign(body))).json()["result"] == "duplicate"
    with sync_session_factory()() as s:
        assert credits.balance(s, uuid.UUID(uid)) == 0


async def test_unknown_user_is_ignored_and_recorded(client):
    body = payload("subscription_created.json", str(uuid.uuid4()), "nobody@example.com", fresh_ids())
    r = await post(client, body, sign(body))
    assert r.status_code == 200 and r.json()["result"] == "ignored"


async def test_checkout_without_config_is_503_and_mock_works(client, monkeypatch):
    u = await register(client)
    r = await client.post("/billing/checkout", json={"plan": "pro"}, headers=u["headers"])
    assert r.status_code == 503 and r.json()["error_code"] == "payments_unavailable"
    monkeypatch.setattr(get_settings(), "payments_provider", "mock")
    r = await client.post("/billing/checkout", json={"plan": "pro"}, headers=u["headers"])
    assert r.status_code == 200 and "mock_checkout=pro" in r.json()["url"]
    r = await client.post("/billing/mock/subscribe", json={"plan": "starter"}, headers=u["headers"])
    assert r.status_code == 200 and r.json()["plan"] == "starter" and r.json()["credits"] == 15
    r = await client.get("/billing/subscription", headers=u["headers"])
    assert r.json()["status"] == "active" and r.json()["subscription_plan"] == "starter"
    assert (await client.get("/billing/portal", headers=u["headers"])).status_code == 200


def test_credit_reservation_under_concurrent_renders():
    """Two renders race for a balance of 1 credit: exactly one reservation succeeds (SELECT … FOR UPDATE)."""
    with sync_session_factory()() as s:
        u = User(email=f"race-{uuid.uuid4().hex[:8]}@example.com", password_hash="x", plan="free", credits=0)
        s.add(u); s.flush()
        credits.grant(s, u.id, 1, "grant")
        pids = []
        for i in range(2):
            p = Project(user_id=u.id, title=f"race {i}", template="steps", size="9:16", size_w=1080, size_h=1920, status="preview_ready", duration_s=30)
            s.add(p); s.flush(); pids.append(p.id)
        s.commit()
        uid = u.id
    results: list[str] = []
    barrier = threading.Barrier(2)

    def worker(pid):
        with sync_session_factory()() as s2:
            p = s2.get(Project, pid)
            barrier.wait()
            try:
                credits.reserve(s2, p, 1); s2.commit(); results.append("ok")
            except credits.InsufficientCredits:
                s2.rollback(); results.append("short")

    ts = [threading.Thread(target=worker, args=(pid,)) for pid in pids]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert sorted(results) == ["ok", "short"]
    with sync_session_factory()() as s:
        assert credits.balance(s, uid) == 0 and s.get(User, uid).credits == 0
        reserved = [s.get(Project, pid).credits_reserved for pid in pids]
        assert sorted(reserved) == [0, 1]
        # release the one that was reserved; commit path on the other is a no-op
        p = next(s.get(Project, pid) for pid in pids if s.get(Project, pid).credits_reserved)
        credits.release(s, p); s.commit()
        assert s.get(User, uid).credits == 1 and credits.balance(s, uid) == 1


def test_plan_gating_render_options():
    from vs_api.services import render_options
    free = User(email="f@example.com", password_hash="x", plan="free")
    pro = User(email="p@example.com", password_hash="x", plan="pro")
    agency = User(email="a@example.com", password_hash="x", plan="agency")
    f, p, a = render_options(free), render_options(pro), render_options(agency)
    assert f["watermark"] and f["max_height"] == 720 and not f["priority"]
    assert p["watermark"] is None and p["max_height"] == 2160 and not p["priority"]
    assert a["priority"] is True
    assert plans.template_allowed("free", "steps") and not plans.template_allowed("free", "recipe", "pro") and plans.template_allowed("pro", "recipe", "pro")
    assert plans.concurrency_limit("free") == 1 and plans.concurrency_limit("agency") == 3
    _ = ADMIN, os
