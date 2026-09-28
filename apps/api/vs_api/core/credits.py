"""Credit ledger with a fast-path balance on users. Sync implementations on a `Session`; the API calls them via `run_sync`.

balance = SUM(credit_ledger.delta) == users.credits (updated in the same transaction; the user row is locked FOR UPDATE).
reserve (delta -n) at queued_render, commit (delta 0, marks the reservation final) at done, release (delta +n) on failure.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import CreditLedger, Project, User


class InsufficientCredits(Exception):
    def __init__(self, needed: int, available: int):
        super().__init__(f"need {needed} credit(s), {available} available")
        self.needed, self.available = needed, available


def _lock_user(s: Session, user_id) -> User:
    return s.execute(select(User).where(User.id == user_id).with_for_update()).scalar_one()


def _add(s: Session, user: User, delta: int, reason: str, project_id=None, external_id: str | None = None, note: str | None = None) -> CreditLedger:
    row = CreditLedger(user_id=user.id, delta=delta, reason=reason, project_id=project_id, external_id=external_id, note=note)
    s.add(row)
    user.credits = (user.credits or 0) + delta
    s.flush()
    return row


def grant(s: Session, user_id, credits: int, reason: str = "grant", external_id: str | None = None, note: str | None = None) -> int:
    """Idempotent when external_id is given (unique)."""
    user = _lock_user(s, user_id)
    if external_id and s.execute(select(CreditLedger.id).where(CreditLedger.external_id == external_id)).first():
        return user.credits
    _add(s, user, credits, reason, external_id=external_id, note=note)
    return user.credits


def reserve(s: Session, project: Project, credits: int) -> int:
    user = _lock_user(s, project.user_id)
    if project.credits_reserved:
        return user.credits  # already reserved (idempotent)
    if (user.credits or 0) < credits:
        raise InsufficientCredits(credits, user.credits or 0)
    _add(s, user, -credits, "reserve", project_id=project.id)
    project.credits_reserved = credits
    return user.credits


def commit(s: Session, project: Project) -> None:
    user = _lock_user(s, project.user_id)
    if not project.credits_reserved:
        return
    _add(s, user, 0, "commit", project_id=project.id, note=f"{project.credits_reserved} credit(s) committed")
    project.credits_committed = project.credits_reserved
    project.credits_reserved = 0


def release(s: Session, project: Project) -> None:
    user = _lock_user(s, project.user_id)
    if not project.credits_reserved:
        return
    _add(s, user, project.credits_reserved, "release", project_id=project.id)
    project.credits_reserved = 0


def balance(s: Session, user_id) -> int:
    return int(s.execute(select(func.coalesce(func.sum(CreditLedger.delta), 0)).where(CreditLedger.user_id == user_id)).scalar_one())


def renew(s: Session, user_id, plan_credits: int, external_id: str, note: str | None = None) -> int:
    """Plan renewal: unused credits do not roll over → reset the balance to the plan's credits (idempotent by external_id)."""
    user = _lock_user(s, user_id)
    if s.execute(select(CreditLedger.id).where(CreditLedger.external_id == external_id)).first():
        return user.credits
    reserved = int(s.execute(select(func.coalesce(func.sum(Project.credits_reserved), 0)).where(Project.user_id == user_id)).scalar_one())
    target = plan_credits - reserved
    _add(s, user, target - (user.credits or 0), "plan_renewal", external_id=external_id, note=note or f"renewal at {datetime.utcnow():%Y-%m-%d}")
    return user.credits
