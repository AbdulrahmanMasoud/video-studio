"""Payments providers: Lemon Squeezy (merchant of record; hosted checkout + webhooks) and a mock for dev/tests.

Webhook events are normalised into `BillingEvent`s and applied by `apply_event` (idempotent per event id).
Only this module knows Lemon Squeezy's payload shapes.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from . import credits, email, plans
from .models import Subscription, User, WebhookEvent

log = logging.getLogger("vs_api.payments")
PLAN_ORDER = ["free", "starter", "pro", "agency"]
ACTIVE_STATUSES = {"active", "on_trial", "past_due", "paused"}


@dataclass
class BillingEvent:
    kind: str                      # subscription_created | subscription_updated | subscription_cancelled | subscription_expired |
    #                                payment_success | payment_failed | order_refunded | unknown
    event_id: str                  # unique id for idempotency
    user_id: str | None = None
    email: str | None = None
    customer_id: str | None = None
    subscription_id: str | None = None
    plan: str | None = None
    status: str | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    invoice_id: str | None = None
    order_id: str | None = None
    portal_url: str | None = None
    raw: dict = field(default_factory=dict)


class PaymentsProvider:
    name = "base"

    def checkout_url(self, user: User, plan: str, locale: str = "en") -> str:
        raise NotImplementedError

    def portal_url(self, user: User, sub: Subscription | None) -> str:
        raise NotImplementedError

    def verify(self, body: bytes, signature: str | None) -> bool:
        raise NotImplementedError

    def parse(self, payload: dict, headers: dict[str, str]) -> BillingEvent:
        raise NotImplementedError


class MockProvider(PaymentsProvider):
    name = "mock"

    def checkout_url(self, user, plan, locale="en"):
        return f"{get_settings().web_origin}/{locale}/app/billing?mock_checkout={plan}"

    def portal_url(self, user, sub):
        return f"{get_settings().web_origin}/app/billing?mock_portal=1"

    def verify(self, body, signature):
        return True

    def parse(self, payload, headers):
        return _parse_lemonsqueezy(payload, headers)  # the mock accepts LS-shaped payloads so tests cover the same path


class LemonSqueezyProvider(PaymentsProvider):
    """https://docs.lemonsqueezy.com — API key, store id, one variant id per paid plan, webhook signing secret."""
    name = "lemonsqueezy"
    API = "https://api.lemonsqueezy.com/v1"

    def __init__(self):
        self.api_key = os.environ.get("LEMONSQUEEZY_API_KEY", "")
        self.store_id = os.environ.get("LEMONSQUEEZY_STORE_ID", "")
        self.secret = os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET", "")
        self.variants = {p: os.environ.get(f"LEMONSQUEEZY_VARIANT_{p.upper()}", "") for p in ("starter", "pro", "agency")}

    def _call(self, method: str, path: str, body: dict | None = None) -> dict:
        req = urllib.request.Request(f"{self.API}{path}", data=json.dumps(body).encode() if body else None, method=method,
                                     headers={"Authorization": f"Bearer {self.api_key}", "Accept": "application/vnd.api+json",
                                              "Content-Type": "application/vnd.api+json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Lemon Squeezy {method} {path} failed ({e.code}): {e.read().decode()[:300]}") from e

    def checkout_url(self, user, plan, locale="en"):
        variant = self.variants.get(plan)
        if not (self.api_key and self.store_id and variant):
            raise RuntimeError("Lemon Squeezy is not configured (LEMONSQUEEZY_API_KEY, LEMONSQUEEZY_STORE_ID, LEMONSQUEEZY_VARIANT_*)")
        s = get_settings()
        body = {"data": {"type": "checkouts",
                         "attributes": {"checkout_data": {"email": user.email, "custom": {"user_id": str(user.id), "plan": plan}},
                                        "product_options": {"redirect_url": f"{s.web_origin}/{locale}/app/billing?checkout=success",
                                                            "receipt_button_text": "Open VideoStudio"},
                                        "checkout_options": {"embed": False}},
                         "relationships": {"store": {"data": {"type": "stores", "id": str(self.store_id)}},
                                           "variant": {"data": {"type": "variants", "id": str(variant)}}}}}
        r = self._call("POST", "/checkouts", body)
        return r["data"]["attributes"]["url"]

    def portal_url(self, user, sub):
        if sub and sub.raw.get("urls", {}).get("customer_portal"):
            # LS portal links are signed and expire; refresh from the API when we can
            try:
                r = self._call("GET", f"/subscriptions/{sub.external_id}")
                return r["data"]["attributes"]["urls"]["customer_portal"]
            except Exception as e:
                log.warning("portal refresh failed: %s", e)
                return sub.raw["urls"]["customer_portal"]
        raise RuntimeError("no active subscription")

    def verify(self, body, signature):
        if not self.secret or not signature:
            return False
        digest = hmac.new(self.secret.encode(), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature.strip())

    def parse(self, payload, headers):
        return _parse_lemonsqueezy(payload, headers)


def _parse_lemonsqueezy(payload: dict, headers: dict[str, str]) -> BillingEvent:
    meta = payload.get("meta") or {}
    name = meta.get("event_name") or headers.get("x-event-name") or "unknown"
    data = payload.get("data") or {}
    attrs = data.get("attributes") or {}
    custom = meta.get("custom_data") or {}
    kinds = {"subscription_created": "subscription_created", "subscription_updated": "subscription_updated", "subscription_cancelled": "subscription_cancelled",
             "subscription_resumed": "subscription_updated", "subscription_expired": "subscription_expired", "subscription_paused": "subscription_updated",
             "subscription_unpaused": "subscription_updated", "subscription_payment_success": "payment_success", "subscription_payment_failed": "payment_failed",
             "subscription_payment_recovered": "payment_success", "order_refunded": "order_refunded", "order_created": "order_created"}
    kind = kinds.get(name, "unknown")
    # LS has no event id: hash the body (same event redelivered → same id; updates carry a new updated_at)
    event_id = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:48]
    ev = BillingEvent(kind=kind, event_id=event_id, raw=attrs, user_id=custom.get("user_id"), email=attrs.get("user_email"),
                      customer_id=str(attrs["customer_id"]) if attrs.get("customer_id") else None)
    variant = str(attrs.get("variant_id") or "")
    # the variant is the truth (plan changes in the portal change the variant); custom_data.plan was set at checkout time
    ev.plan = _plan_for_variant(variant) or custom.get("plan") or None
    if kind.startswith("subscription"):
        ev.subscription_id = str(data.get("id") or "")
        ev.status = attrs.get("status")
        ev.cancel_at_period_end = bool(attrs.get("cancelled"))
        ev.current_period_end = _dt(attrs.get("ends_at") or attrs.get("renews_at"))
        ev.portal_url = (attrs.get("urls") or {}).get("customer_portal")
    elif kind in ("payment_success", "payment_failed"):
        ev.subscription_id = str(attrs.get("subscription_id") or "")
        ev.invoice_id = str(data.get("id") or "")
        ev.status = attrs.get("status")
    elif kind in ("order_refunded", "order_created"):
        ev.order_id = str(data.get("id") or "")
        first = ((attrs.get("first_order_item") or {}).get("variant_id"))
        ev.plan = ev.plan or _plan_for_variant(str(first or "")) or None
    return ev


def _plan_for_variant(variant_id: str) -> str | None:
    if not variant_id:
        return None
    for p in ("starter", "pro", "agency"):
        if os.environ.get(f"LEMONSQUEEZY_VARIANT_{p.upper()}", "") == variant_id:
            return p
    return None


def _dt(v: Any) -> datetime | None:
    if not v:
        return None
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None


def provider() -> PaymentsProvider:
    return LemonSqueezyProvider() if get_settings().payments_provider == "lemonsqueezy" else MockProvider()


# ---------------------------------------------------------------- applying events (sync, inside a transaction)
def _find_user(s: Session, ev: BillingEvent) -> User | None:
    if ev.user_id:
        u = s.get(User, ev.user_id)
        if u:
            return u
    if ev.subscription_id:
        sub = s.execute(select(Subscription).where(Subscription.external_id == ev.subscription_id)).scalar_one_or_none()
        if sub:
            return s.get(User, sub.user_id)
    if ev.customer_id:
        u = s.execute(select(User).where(User.ls_customer_id == ev.customer_id).order_by(User.created_at.desc())).scalars().first()
        if u:
            return u
    if ev.email:
        return s.execute(select(User).where(User.email == ev.email.lower())).scalar_one_or_none()
    return None


def record_and_apply(s: Session, provider_name: str, ev: BillingEvent, payload: dict) -> str:
    """Store the webhook (unique by event id) and apply it exactly once. Returns 'applied' | 'duplicate' | 'ignored'."""
    if s.execute(select(WebhookEvent.id).where(WebhookEvent.external_event_id == ev.event_id)).first():
        return "duplicate"
    row = WebhookEvent(provider=provider_name, external_event_id=ev.event_id, payload=payload)
    s.add(row); s.flush()
    try:
        result = apply_event(s, ev)
        row.processed_at = datetime.utcnow()
        return result
    except Exception as e:
        row.error = str(e)[:2000]
        row.processed_at = datetime.utcnow()
        log.exception("webhook %s failed", ev.kind)
        return "error"


def apply_event(s: Session, ev: BillingEvent) -> str:
    user = _find_user(s, ev)
    if not user:
        log.warning("webhook %s: no matching user (%s)", ev.kind, ev.email)
        return "ignored"
    if ev.customer_id and not user.ls_customer_id:
        user.ls_customer_id = ev.customer_id
    if ev.kind in ("subscription_created", "subscription_updated", "subscription_cancelled", "subscription_expired"):
        sub = s.execute(select(Subscription).where(Subscription.external_id == ev.subscription_id)).scalar_one_or_none()
        if sub is None:
            sub = Subscription(user_id=user.id, provider="lemonsqueezy", external_id=ev.subscription_id or "", plan=ev.plan or user.plan, status=ev.status or "active")
            s.add(sub)
        sub.plan = ev.plan or sub.plan
        sub.status = ev.status or sub.status
        sub.current_period_end = ev.current_period_end or sub.current_period_end
        sub.cancel_at_period_end = ev.cancel_at_period_end or ev.kind == "subscription_cancelled"
        sub.raw = {**(sub.raw or {}), **{k: v for k, v in ev.raw.items() if k in ("urls", "status", "renews_at", "ends_at", "variant_id", "product_name", "variant_name")}}
        if ev.kind == "subscription_expired" or sub.status == "expired":
            # downgrade applies at period end: LS sends `expired` when the paid period is over
            user.plan = "free"
            credits.renew(s, user.id, int(plans.plan("free")["credits"]), external_id=f"expire:{sub.external_id}:{ev.event_id[:12]}", note="subscription expired")
        elif sub.status in ACTIVE_STATUSES and sub.plan in PLAN_ORDER:
            if ev.kind == "subscription_created" and user.plan != sub.plan:
                user.plan = sub.plan
            elif ev.kind == "subscription_updated":
                user.plan = sub.plan   # upgrades/downgrades done in the portal take effect with the next invoice; LS updates the variant then
        s.flush()
        return "applied"
    if ev.kind == "payment_success":
        sub = s.execute(select(Subscription).where(Subscription.external_id == ev.subscription_id)).scalar_one_or_none()
        plan_name = (sub.plan if sub else None) or ev.plan or user.plan
        if plan_name in PLAN_ORDER and plan_name != "free":
            user.plan = plan_name
            credits.renew(s, user.id, int(plans.plan(plan_name)["credits"]), external_id=f"invoice:{ev.invoice_id}", note=f"{plan_name} renewal")
        return "applied"
    if ev.kind == "payment_failed":
        email.send(user.email, "payment_failed", user.locale, link=f"{get_settings().web_origin}/app/billing")
        return "applied"
    if ev.kind == "order_refunded":
        plan_name = ev.plan or user.plan
        if plan_name in PLAN_ORDER and plan_name != "free":
            n = int(plans.plan(plan_name)["credits"])
            credits.grant(s, user.id, -min(n, max(0, user.credits)), "refund", external_id=f"refund:{ev.order_id}", note=f"refund of {plan_name}")
        user.plan = "free"
        for sub in s.execute(select(Subscription).where(Subscription.user_id == user.id)).scalars():
            sub.status = "refunded"
        return "applied"
    return "ignored"
