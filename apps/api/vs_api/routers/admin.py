"""Admin endpoints (X-Admin-Key): LLM routing, credits, template flags, failed jobs, template requests."""
from __future__ import annotations

import os

from fastapi import APIRouter, Query
from sqlalchemy import select

from ..core import credits
from ..core.llm_settings import LLMSettings, provider_status
from ..core.models import AppSetting, Project, TemplateFlag, TemplateRequest, User, WebhookEvent
from ..deps import DB, Admin, err
from ..routers.auth import user_out
from ..schemas import GrantCreditsIn, LLMSettingsIn, LLMSettingsOut, Msg, ToggleTemplateIn, UserOut

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[])
LLM_KEYS = ["llm.planner_model", "llm.fast_model", "llm.vision_model", "llm.free_tier_model", "llm.fallback_chain"]


async def llm_rows(db) -> dict:
    rows = (await db.execute(select(AppSetting).where(AppSetting.key.in_(LLM_KEYS)))).scalars().all()
    return {r.key: r.value for r in rows}


@router.get("/llm", response_model=LLMSettingsOut)
async def get_llm(_: Admin, db: DB):
    overrides = await llm_rows(db)
    effective = LLMSettings.from_env(overrides=overrides)
    return LLMSettingsOut(settings=effective.to_dict(), defaults=LLMSettings.from_env().to_dict(), providers=provider_status())


@router.put("/llm", response_model=LLMSettingsOut)
async def put_llm(_: Admin, body: LLMSettingsIn, db: DB):
    updates = {f"llm.{k}": v for k, v in body.model_dump(exclude_none=True).items()}
    for k, v in updates.items():
        if isinstance(v, str) and ("/" not in v or " " in v):
            raise err(422, "invalid_model", f"{k}: use a LiteLLM model string like anthropic/claude-sonnet-5")
        row = await db.get(AppSetting, k)
        if row is None:
            db.add(AppSetting(key=k, value=v))
        else:
            row.value = v
    await db.commit()
    return await get_llm(_, db)


@router.post("/grant-credits", response_model=UserOut)
async def grant_credits(_: Admin, body: GrantCreditsIn, db: DB):
    if not body.email and not body.user_id:
        raise err(422, "user_required", "give email or user_id")
    q = select(User).where(User.email == body.email.lower()) if body.email else select(User).where(User.id == body.user_id)
    user = (await db.execute(q)).scalar_one_or_none()
    if not user:
        raise err(404, "not_found", "user not found")
    await db.run_sync(lambda s: credits.grant(s, user.id, body.credits, "admin", note=body.note))
    await db.commit(); await db.refresh(user)
    return user_out(user)


@router.post("/toggle-template", response_model=Msg)
async def toggle_template(_: Admin, body: ToggleTemplateIn, db: DB):
    from ..core import catalog
    if catalog.by_name(body.name) is None:
        raise err(404, "not_found", f"unknown template {body.name}")
    flag = await db.get(TemplateFlag, body.name)
    if flag is None:
        flag = TemplateFlag(name=body.name); db.add(flag)
    flag.enabled = body.enabled
    if body.tier_required:
        flag.tier_required = body.tier_required
    await db.commit()
    return Msg(message=f"{body.name}: enabled={flag.enabled}, tier={flag.tier_required}")


@router.get("/failed")
async def list_failed(_: Admin, db: DB, limit: int = Query(50, le=200)):
    rows = (await db.execute(select(Project).where(Project.status == "failed", Project.deleted_at.is_(None)).order_by(Project.updated_at.desc()).limit(limit))).scalars().all()
    return [{"id": str(p.id), "user_id": str(p.user_id), "title": p.title, "template": p.template, "error_code": p.error_code, "error_message": p.error_message,
             "stage": p.failed_stage, "attempts": p.attempts, "updated_at": p.updated_at, "rq_job_id": p.rq_job_id} for p in rows]


@router.get("/template-requests")
async def list_template_requests(_: Admin, db: DB, limit: int = Query(100, le=500)):
    rows = (await db.execute(select(TemplateRequest, User.email).join(User, User.id == TemplateRequest.user_id).order_by(TemplateRequest.created_at.desc()).limit(limit))).all()
    return [{"id": str(r.id), "email": email, "description": r.description, "example_url": r.example_url, "file_key": r.file_key, "status": r.status,
             "created_at": r.created_at} for r, email in rows]


@router.get("/env")
async def env_info(_: Admin):
    keys = ["APP_ENV", "PLANNER_MODE", "WHISPER_MODEL", "PAYMENTS_PROVIDER", "TTS_PROVIDER", "EMAIL_PROVIDER"]
    return {k: os.environ.get(k) for k in keys}


@router.get("/webhooks")
async def list_webhooks(_: Admin, db: DB, limit: int = Query(50, le=500)):
    rows = (await db.execute(select(WebhookEvent).order_by(WebhookEvent.created_at.desc()).limit(limit))).scalars().all()
    return [{"id": str(w.id), "provider": w.provider, "event": (w.payload.get("meta") or {}).get("event_name"), "external_event_id": w.external_event_id,
             "processed_at": w.processed_at, "error": w.error, "created_at": w.created_at} for w in rows]
