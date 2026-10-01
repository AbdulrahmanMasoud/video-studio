"""Template catalog (enabled templates + flags, sizes, platforms, languages, limits)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from ..core import catalog, plans
from ..core.models import TemplateFlag, User
from ..deps import DB, optional_user
from ..schemas import CatalogOut, LanguageOut, SizeOut, TemplateOut

router = APIRouter(prefix="/templates", tags=["templates"])


async def flags(db) -> dict[str, TemplateFlag]:
    return {f.name: f for f in (await db.execute(select(TemplateFlag))).scalars()}


def template_out(t: dict, flag: TemplateFlag | None, user: User | None) -> TemplateOut:
    enabled = bool(flag.enabled) if flag else False
    tier = flag.tier_required if flag else "pro"
    available = enabled and (user is None or plans.template_allowed(user.plan, t["name"], tier))
    return TemplateOut(name=t["name"], title=t.get("title", t["name"]), category=t.get("category", ""), summary=t.get("summary", ""),
                       scenes=t.get("scenes", []), media_fields=t.get("media_fields", []), needs_media=t.get("needs_media", []),
                       has_ar_example=bool(t.get("has_ar_example")), preview=t.get("preview", f"/previews/{t['name']}.jpg"), enabled=enabled,
                       tier_required=tier, available=available)


@router.get("", response_model=CatalogOut)
async def list_templates(db: DB, user: Annotated[User | None, Depends(optional_user)] = None, include_disabled: bool = False):
    fl = await flags(db)
    items = [template_out(t, fl.get(t["name"]), user) for t in catalog.templates()]
    if not include_disabled:
        items = [t for t in items if t.enabled]
    return CatalogOut(templates=items, sizes=[SizeOut(**s) for s in catalog.SIZES], platforms=catalog.PLATFORMS, languages=[LanguageOut(**lang) for lang in catalog.LANGUAGES],
                      limits=plans.limits())
