"""Billing: plans, checkout, portal, webhooks (provider-specific parts land in Phase 5; the mock provider works now)."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..config import get_settings
from ..core import credits, plans
from ..core.models import Project, User
from ..deps import DB, CurrentUser, err
from ..routers.auth import user_out
from ..schemas import CheckoutIn, CheckoutOut, MockSubscribeIn, PlanOut, UserOut

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plans", response_model=list[PlanOut])
async def list_plans():
    return [PlanOut(name=k, **{kk: v[kk] for kk in ("price_usd", "credits", "max_res", "watermark", "templates")},
                    brand_kit=bool(v.get("brand_kit")), priority_queue=bool(v.get("priority_queue"))) for k, v in plans.plans().items()]


@router.post("/checkout", response_model=CheckoutOut)
async def checkout(body: CheckoutIn, user: CurrentUser):
    s = get_settings()
    if s.payments_provider == "mock":
        return CheckoutOut(url=f"{s.web_origin}/app/billing?mock_checkout={body.plan}")
    raise err(501, "not_implemented", "Lemon Squeezy checkout arrives in Phase 5")


@router.get("/portal", response_model=CheckoutOut)
async def portal(user: CurrentUser):
    s = get_settings()
    if s.payments_provider == "mock":
        return CheckoutOut(url=f"{s.web_origin}/app/billing?mock_portal=1")
    raise err(501, "not_implemented", "Lemon Squeezy portal arrives in Phase 5")


@router.post("/mock/subscribe", response_model=UserOut)
async def mock_subscribe(body: MockSubscribeIn, user: CurrentUser, db: DB):
    """Dev/test only: switch the plan and renew credits as a successful payment would."""
    if get_settings().payments_provider != "mock":
        raise err(404, "not_found", "not available")
    import uuid

    def _tx(s):
        u = s.get(User, user.id)
        u.plan = body.plan
        credits.renew(s, u.id, int(plans.plan(body.plan)["credits"]), external_id=f"mock:{uuid.uuid4().hex}", note=f"mock subscribe {body.plan}")
        _ = Project
    await db.run_sync(_tx)
    await db.commit(); await db.refresh(user)
    return user_out(user)


@router.post("/webhooks/lemonsqueezy")
async def lemonsqueezy_webhook(request: Request):
    raise err(501, "not_implemented", "Lemon Squeezy webhooks arrive in Phase 5")
