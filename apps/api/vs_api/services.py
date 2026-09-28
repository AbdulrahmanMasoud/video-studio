"""Project services shared by the routers: creation, gating, enqueueing, serialisation."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from .config import get_settings
from .core import catalog, credits, plans, queue, state, storage
from .core.models import Project, ProjectAsset, TemplateFlag, User
from .deps import err
from .schemas import AssetOut, ProjectDetailOut, ProjectOut

ACTIVE = {"queued_transcribe", "transcribing", "editing", "planning", "queued_render", "rendering"}
SIZE_PRESETS = {"9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350), "16:9": (1920, 1080)}


def parse_size(size: str) -> tuple[int, int]:
    s = size.strip().lower()
    if s in SIZE_PRESETS:
        return SIZE_PRESETS[s]
    import re
    m = re.match(r"^(\d{3,4})x(\d{3,4})$", s)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        if 320 <= w <= 3840 and 320 <= h <= 3840:
            return w - w % 2, h - h % 2
    m = re.match(r"^(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)$", s)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        if a <= b:
            w, h = 1080, round(1080 * b / a)
        else:
            w, h = round(1080 * a / b), 1080
        return w - w % 2, h - h % 2
    raise err(422, "invalid_size", "size must be 9:16, 1:1, 4:5, 16:9, a ratio like 4:3 or WxH")


async def template_flag(db: AsyncSession, name: str) -> TemplateFlag | None:
    return (await db.execute(select(TemplateFlag).where(TemplateFlag.name == name))).scalar_one_or_none()


async def check_template(db: AsyncSession, user: User, name: str) -> None:
    if catalog.by_name(name) is None:
        raise err(422, "unknown_template", f"unknown template {name!r}")
    flag = await template_flag(db, name)
    if not flag or not flag.enabled:
        raise err(422, "template_disabled", f"template {name!r} is not available yet")
    if not plans.template_allowed(user.plan, name, flag.tier_required):
        raise err(402, "plan_required", f"template {name!r} needs a higher plan")


async def active_jobs(db: AsyncSession, user_id) -> int:
    return int((await db.execute(select(func.count()).select_from(Project).where(Project.user_id == user_id, Project.status.in_(ACTIVE)))).scalar_one())


async def check_concurrency(db: AsyncSession, user: User) -> None:
    if await active_jobs(db, user.id) >= plans.concurrency_limit(user.plan):
        raise err(429, "too_many_jobs", f"you can run {plans.concurrency_limit(user.plan)} job(s) at a time on the {user.plan} plan; wait for one to finish")


def owns_key(user: User, key: str, prefix: str) -> bool:
    return key.startswith(f"{prefix}/{user.id}/") and ".." not in key


def render_options(user: User) -> dict:
    rules = plans.render_rules(user.plan)
    s = get_settings()
    return {"watermark": s.watermark_path if rules["watermark"] else None, "max_height": rules["max_res"], "priority": rules["priority_queue"]}


def enqueue_preview(project: Project, user: User) -> str:
    s = get_settings()
    job = queue.enqueue("transcribe", "vs_worker.tasks.preview_job", str(project.id), priority=render_options(user)["priority"],
                        timeout=s.job_timeout_transcribe_s + s.job_timeout_plan_s + 120, job_id=f"preview-{project.id}-{project.attempts}")
    return job.id


def enqueue_render(project: Project, user: User) -> str:
    s = get_settings()
    job = queue.enqueue("render", "vs_worker.tasks.render_job", str(project.id), priority=render_options(user)["priority"],
                        timeout=s.job_timeout_render_s + 300, job_id=f"render-{project.id}-{project.attempts}")
    return job.id


def enqueue_edit(project: Project, user: User, kind: str, payload: dict) -> str:
    s = get_settings()
    job = queue.enqueue("plan", "vs_worker.tasks.edit_job", str(project.id), kind, payload, priority=render_options(user)["priority"],
                        timeout=s.job_timeout_plan_s + 120, job_id=f"edit-{project.id}-{uuid.uuid4().hex[:8]}")
    return job.id


async def presigned(key: str | None, filename: str | None = None) -> str | None:
    if not key:
        return None
    return await run_in_threadpool(storage.presign_download, key, filename)


def _base_fields(p: Project) -> dict[str, Any]:
    return {"id": p.id, "title": p.title, "template": p.template, "lang": p.lang, "detected_lang": p.detected_lang, "size": p.size, "size_w": p.size_w,
            "size_h": p.size_h, "platform": p.platform, "brief": p.brief or {}, "status": p.status, "progress": p.progress, "input_kind": p.input_kind,
            "has_script": bool(p.script), "duration_s": float(p.duration_s) if p.duration_s is not None else None, "credits_reserved": p.credits_reserved,
            "credits_committed": p.credits_committed, "credits_needed": plans.credits_for_duration(float(p.duration_s)) if p.duration_s else None,
            "planner": p.planner, "llm_model": p.llm_model, "llm_cost_usd": float(p.llm_cost_usd or 0), "error_code": p.error_code,
            "error_message": p.error_message, "failed_stage": p.failed_stage, "attempts": p.attempts, "output_size": p.output_size, "created_at": p.created_at,
            "updated_at": p.updated_at, "done_at": p.done_at}


async def project_out(p: Project, with_urls: bool = True) -> ProjectOut:
    d = _base_fields(p)
    if with_urls:
        d["preview_url"] = await presigned(p.preview_key)
        d["sheet_url"] = await presigned(p.sheet_key)
    return ProjectOut(**d)


def asset_out(a: ProjectAsset, thumb: str | None = None) -> AssetOut:
    return AssetOut(id=a.id, name=a.name, kind=a.kind, original_name=a.original_name, mime=a.mime, bytes=a.bytes, width=a.width, height=a.height,
                    duration_s=float(a.duration_s) if a.duration_s is not None else None, has_alpha=a.has_alpha, description=a.description,
                    description_source=a.description_source, status=a.status, error=a.error, thumbnail_url=thumb)


async def project_detail_out(db: AsyncSession, p: Project) -> ProjectDetailOut:
    d = _base_fields(p)
    d["preview_url"] = await presigned(p.preview_key)
    d["sheet_url"] = await presigned(p.sheet_key)
    assets = (await db.execute(select(ProjectAsset).where(ProjectAsset.project_id == p.id).order_by(ProjectAsset.created_at))).scalars().all()
    outs = []
    for a in assets:
        thumb = await presigned(a.key) if a.kind == "image" and a.status in ("uploaded", "ready") else None
        outs.append(asset_out(a, thumb))
    used = {s.get("asset") for s in (p.asset_slots or []) if s.get("asset")}
    unused = [a.name for a in assets if a.status == "ready" and a.name not in used]
    return ProjectDetailOut(**d, plan=p.plan, editable_fields=p.editable_fields, asset_slots=p.asset_slots, unused_assets=unused, words=p.words,
                            assets=outs, qa=p.qa)


async def get_owned_project(db: AsyncSession, user: User, project_id: uuid.UUID) -> Project:
    p = (await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id, Project.deleted_at.is_(None)))).scalar_one_or_none()
    if not p:
        raise err(404, "not_found", "project not found")
    return p


async def reserve_and_queue_render(db: AsyncSession, user: User, p: Project) -> str:
    """preview_ready → queued_render with credits reserved in the same transaction; then enqueue."""
    needed = plans.credits_for_duration(float(p.duration_s or 0))

    def _tx(s):
        sp = s.get(Project, p.id)
        credits.reserve(s, sp, needed)
        sp.attempts += 1
        state.transition(s, sp, "queued_render", {"credits": needed})
        return sp.attempts

    try:
        await db.run_sync(_tx)
    except credits.InsufficientCredits as e:
        await db.rollback()
        raise err(402, "insufficient_credits", f"this video needs {e.needed} credit(s); you have {e.available}") from e
    await db.commit()
    await db.refresh(p)
    job_id = await run_in_threadpool(enqueue_render, p, user)
    p.rq_job_id = job_id
    await db.commit()
    return job_id
