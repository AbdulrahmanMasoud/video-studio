"""Current user: profile, plan, brand kit, delete account."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Response
from sqlalchemy import select

from ..config import get_settings
from ..core import plans
from ..core.models import BrandKit, Project, User
from ..core.security import verify_password
from ..deps import DB, CurrentUser, err
from ..routers.auth import clear_session_cookies, user_out
from ..schemas import BrandKitIn, BrandKitOut, DeleteMeIn, FeaturesOut, LimitsOut, MeOut, Msg, PlanInfo, UpdateMeIn, UserOut

router = APIRouter(prefix="/me", tags=["me"])


def _features() -> FeaturesOut:
    s = get_settings()
    return FeaturesOut(tts=bool(s.tts_enabled and s.tts_provider != "none"), google_oauth=s.google_oauth_enabled, payments_provider=s.payments_provider)


async def _me(db, user: User) -> MeOut:
    bk = (await db.execute(select(BrandKit).where(BrandKit.user_id == user.id))).scalar_one_or_none()
    rules = plans.render_rules(user.plan)
    raw_limits = {k: v for k, v in plans.limits().items() if not isinstance(v, dict)}
    lim = LimitsOut(**raw_limits, concurrent_jobs=plans.concurrency_limit(user.plan), projects_per_hour=plans.projects_per_hour(user.plan))
    return MeOut(user=user_out(user), plan=PlanInfo(**{**plans.plan(user.plan), **rules}),
                 brand_kit=BrandKitOut(palette=bk.palette, fonts=bk.fonts, logo_key=bk.logo_key, updated_at=bk.updated_at) if bk else None,
                 limits=lim, features=_features())


@router.get("", response_model=MeOut)
async def me(user: CurrentUser, db: DB):
    return await _me(db, user)


@router.patch("", response_model=UserOut)
async def update_me(body: UpdateMeIn, user: CurrentUser, db: DB):
    if body.locale:
        user.locale = body.locale
    await db.commit()
    return user_out(user)


@router.put("/brand-kit", response_model=BrandKitOut)
async def put_brand_kit(body: BrandKitIn, user: CurrentUser, db: DB):
    if not plans.render_rules(user.plan)["brand_kit"]:
        raise err(402, "plan_required", "brand kits are available on the Pro and Agency plans")
    for k, v in body.palette.items():
        if not (isinstance(v, str) and v.startswith("#") and len(v) in (4, 7)):
            raise err(422, "invalid_color", f"palette.{k} must be a hex color")
    bk = (await db.execute(select(BrandKit).where(BrandKit.user_id == user.id))).scalar_one_or_none()
    if bk is None:
        bk = BrandKit(user_id=user.id); db.add(bk)
    bk.palette, bk.fonts, bk.logo_key = body.palette, body.fonts, body.logo_key
    await db.commit(); await db.refresh(bk)
    return BrandKitOut(palette=bk.palette, fonts=bk.fonts, logo_key=bk.logo_key, updated_at=bk.updated_at)


@router.delete("", response_model=Msg)
async def delete_me(body: DeleteMeIn, response: Response, user: CurrentUser, db: DB):
    if not verify_password(body.password, user.password_hash):
        raise err(401, "bad_credentials", "wrong password")
    user.deleted_at = datetime.utcnow()
    user.email = f"deleted-{user.id.hex}@deleted.invalid"
    for p in (await db.execute(select(Project).where(Project.user_id == user.id, Project.deleted_at.is_(None)))).scalars():
        p.deleted_at = datetime.utcnow()
    await db.commit()
    clear_session_cookies(response)
    return Msg(message="account deleted")
