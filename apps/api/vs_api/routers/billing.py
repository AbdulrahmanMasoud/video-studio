"""Billing: plans, checkout, portal, subscription status, Lemon Squeezy webhooks (HMAC verified, idempotent), mock provider."""
from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Request
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from ..config import get_settings
from ..core import credits, payments, plans
from ..core.models import Subscription, User
from ..deps import DB, CurrentUser, err
from ..routers.auth import user_out
from ..schemas import CheckoutIn, CheckoutOut, MockSubscribeIn, PlanOut, SubscriptionOut, UserOut

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=list[PlanOut])
async def list_plans():
    return [PlanOut(name=k, **{kk: v[kk] for kk in ("price_usd", "credits", "max_res", "watermark", "templates")},
                    brand_kit=bool(v.get("brand_kit")), priority_queue=bool(v.get("priority_queue"))) for k, v in plans.plans().items()]


@router.post("/checkout", response_model=CheckoutOut)
async def checkout(body: CheckoutIn, user: CurrentUser):
    p = payments.provider()
    try:
        url = await run_in_threadpool(p.checkout_url, user, body.plan, user.locale)
    except RuntimeError as e:
        raise err(503, "payments_unavailable", str(e)) from e
    return CheckoutOut(url=url)


async def _current_sub(db, user: User) -> Subscription | None:
    rows = (await db.execute(select(Subscription).where(Subscription.user_id == user.id).order_by(Subscription.updated_at.desc()))).scalars().all()
    for r in rows:
        if r.status in payments.ACTIVE_STATUSES or r.status == "cancelled":
            return r
    return rows[0] if rows else None


@router.get("/portal", response_model=CheckoutOut)
async def portal(user: CurrentUser, db: DB):
    p = payments.provider()
    sub = await _current_sub(db, user)
    try:
        url = await run_in_threadpool(p.portal_url, user, sub)
    except RuntimeError as e:
        raise err(409, "no_subscription", str(e)) from e
    return CheckoutOut(url=url)


@router.get("/subscription", response_model=SubscriptionOut)
async def subscription(user: CurrentUser, db: DB):
    sub = await _current_sub(db, user)
    return SubscriptionOut(plan=user.plan, credits=user.credits, provider=get_settings().payments_provider, status=sub.status if sub else None,
                           subscription_plan=sub.plan if sub else None, current_period_end=sub.current_period_end if sub else None,
                           cancel_at_period_end=bool(sub.cancel_at_period_end) if sub else False)


@router.post("/mock/subscribe", response_model=UserOut)
async def mock_subscribe(body: MockSubscribeIn, user: CurrentUser, db: DB):
    """Dev/test only: switch the plan and renew credits as a successful payment would."""
    if get_settings().payments_provider != "mock":
        raise err(404, "not_found", "not available")

    def _tx(s):
        u = s.get(User, user.id)
        u.plan = body.plan
        credits.renew(s, u.id, int(plans.plan(body.plan)["credits"]), external_id=f"mock:{uuid.uuid4().hex}", note=f"mock subscribe {body.plan}")
        sub = s.execute(select(Subscription).where(Subscription.user_id == u.id, Subscription.provider == "mock")).scalar_one_or_none()
        if body.plan == "free":
            if sub:
                sub.status = "expired"
        else:
            if sub is None:
                sub = Subscription(user_id=u.id, provider="mock", external_id=f"mock-{u.id}", plan=body.plan, status="active"); s.add(sub)
            sub.plan, sub.status, sub.cancel_at_period_end = body.plan, "active", False
    await db.run_sync(_tx)
    await db.commit(); await db.refresh(user)
    return user_out(user)


@router.post("/webhooks/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request, db: DB):
    """Verified with the signing secret (X-Signature, HMAC-SHA256 of the raw body), stored in webhook_events, applied once."""
    body = await request.body()
    p = payments.provider()
    if not p.verify(body, request.headers.get("X-Signature")):
        raise err(401, "bad_signature", "invalid webhook signature")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        raise err(400, "bad_payload", "invalid JSON") from e
    ev = p.parse(payload, {k.lower(): v for k, v in request.headers.items()})
    result = await db.run_sync(lambda s: payments.record_and_apply(s, p.name, ev, payload))
    await db.commit()
    return {"ok": result != "error", "result": result, "event": ev.kind}
