"""Projects: create (enqueues the preview), list, get, delete, events (SSE), texts, asset slots, render, retry, download."""
from __future__ import annotations

import asyncio
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Query, Request
from sqlalchemy import func, select
from sse_starlette.sse import EventSourceResponse
from starlette.concurrency import run_in_threadpool

from .. import services as svc
from ..config import get_settings
from ..core import plans, state, storage
from ..core.db import async_session_factory
from ..core.models import JobEvent, Project, ProjectAsset
from ..deps import DB, CurrentUser, VerifiedUser, err
from ..ratelimit import check_user_limit
from ..schemas import AssetSlotsIn, DownloadOut, EnqueuedOut, Msg, ProjectCreateIn, ProjectDetailOut, ProjectListOut, ProjectOut, TextsIn

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=EnqueuedOut, status_code=201)
async def create_project(body: ProjectCreateIn, user: VerifiedUser, db: DB):
    s = get_settings()
    check_user_limit(user.id, "projects", plans.projects_per_hour(user.plan))
    await svc.check_template(db, user, body.template)
    if body.platform not in ("tiktok", "reels", "shorts", "youtube", "linkedin", "x", "none"):
        raise err(422, "invalid_platform", "unknown platform")
    w, h = svc.parse_size(body.size)
    if not body.input_key and not body.script:
        raise err(422, "input_required", "upload a recording (input_key) or paste a script")
    if body.script and not body.input_key and not (s.tts_enabled and s.tts_provider != "none"):
        raise err(422, "tts_disabled", "AI voice is not enabled; upload a recording")
    input_kind = None
    if body.input_key:
        if not svc.owns_key(user, body.input_key, "inputs"):
            raise err(422, "invalid_input_key", "input_key does not belong to you")
        info = await run_in_threadpool(storage.head, body.input_key)
        if not info:
            raise err(422, "input_missing", "the upload was not found; upload again")
        if info["size"] > int(plans.limits().get("input_max_mb", 200)) * 1024 * 1024:
            raise err(413, "file_too_large", "input exceeds the size limit")
        input_kind = "video" if info["content_type"].startswith("video/") else "audio"
    await svc.check_concurrency(db, user)
    p = Project(user_id=user.id, title=body.title.strip(), template=body.template, lang=(body.lang or None), size=body.size.lower(), size_w=w, size_h=h,
                platform=body.platform, brief=body.brief, input_key=body.input_key, input_kind=input_kind, script=body.script, status="created", progress=0)
    db.add(p)
    await db.flush()

    def _tx(sess):
        sp = sess.get(Project, p.id)
        sp.attempts = 1
        state.transition(sess, sp, "queued_transcribe", {"input_kind": input_kind, "script": bool(body.script)})
    await db.run_sync(_tx)
    await db.commit()
    await db.refresh(p)
    job_id = await run_in_threadpool(svc.enqueue_preview, p, user)
    p.rq_job_id = job_id
    await db.commit()
    await db.refresh(p)
    return EnqueuedOut(project=await svc.project_out(p), job_id=job_id)


@router.get("", response_model=ProjectListOut)
async def list_projects(user: CurrentUser, db: DB, limit: Annotated[int, Query(ge=1, le=100)] = 50, offset: Annotated[int, Query(ge=0)] = 0,
                        status: str | None = None):
    q = select(Project).where(Project.user_id == user.id, Project.deleted_at.is_(None))
    if status:
        q = q.where(Project.status == status)
    total = int((await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one())
    rows = (await db.execute(q.order_by(Project.created_at.desc()).limit(limit).offset(offset))).scalars().all()
    return ProjectListOut(items=[await svc.project_out(p, with_urls=False) for p in rows], total=total)


@router.get("/{project_id}", response_model=ProjectDetailOut)
async def get_project(project_id: uuid.UUID, user: CurrentUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    return await svc.project_detail_out(db, p)


@router.delete("/{project_id}", response_model=Msg)
async def delete_project(project_id: uuid.UUID, user: CurrentUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    from datetime import datetime

    from ..core import credits, queue
    if p.rq_job_id and p.status in svc.ACTIVE:
        await run_in_threadpool(queue.cancel, p.rq_job_id)

    def _tx(s):
        sp = s.get(Project, p.id)
        credits.release(s, sp)
        sp.deleted_at = datetime.utcnow()
        if sp.status in svc.ACTIVE:
            state.fail(s, sp, "cancelled", "deleted by the user", sp.failed_stage or "preview")
    await db.run_sync(_tx)
    await db.commit()
    await run_in_threadpool(storage.delete_prefix, f"outputs/{user.id}/{p.id}/")
    await run_in_threadpool(storage.delete_prefix, f"assets/{user.id}/{p.id}/")
    if p.input_key:
        await run_in_threadpool(storage.delete, p.input_key)
    return Msg(message="project deleted")


@router.get("/{project_id}/events")
async def events(project_id: uuid.UUID, user: CurrentUser, db: DB, request: Request):
    """Server-sent events: one `status` event per job_events row (+ current state first), heartbeats, ends on done/failed."""
    p = await svc.get_owned_project(db, user, project_id)
    last_id = 0

    async def gen():
        nonlocal last_id
        yield {"event": "status", "data": json.dumps({"status": p.status, "progress": p.progress, "error_code": p.error_code}, default=str)}
        idle = 0
        while True:
            if await request.is_disconnected():
                return
            async with async_session_factory()() as s:
                rows = (await s.execute(select(JobEvent).where(JobEvent.project_id == project_id, JobEvent.id > last_id).order_by(JobEvent.id))).scalars().all()
                cur = (await s.execute(select(Project.status, Project.progress, Project.error_code, Project.error_message).where(Project.id == project_id))).first()
            for ev in rows:
                last_id = ev.id
                yield {"event": "status", "id": str(ev.id), "data": json.dumps({"status": ev.to_status, "from": ev.from_status, "progress": cur[1] if cur else None,
                                                                                  "detail": ev.detail, "at": ev.created_at.isoformat()}, default=str)}
            if cur and cur[0] in ("done", "failed") and not rows:
                yield {"event": "end", "data": json.dumps({"status": cur[0], "progress": cur[1], "error_code": cur[2], "error_message": cur[3]})}
                return
            if not rows:
                idle += 1
                if idle % 15 == 0:
                    yield {"event": "heartbeat", "data": json.dumps({"progress": cur[1] if cur else None, "status": cur[0] if cur else None})}
            else:
                idle = 0
            await asyncio.sleep(1.0)

    return EventSourceResponse(gen())


def _require_preview_ready(p: Project) -> None:
    if p.status != "preview_ready":
        raise err(409, "not_preview_ready", f"the project is {p.status}; edits are possible only when the preview is ready")


@router.post("/{project_id}/texts", response_model=EnqueuedOut)
async def edit_texts(project_id: uuid.UUID, body: TextsIn, user: CurrentUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    _require_preview_ready(p)
    allowed = {f["path"]: f for f in (p.editable_fields or [])}
    for f in body.fields:
        if f.path not in allowed:
            raise err(422, "field_not_editable", f"{f.path} is not an editable field")
        if len(f.value) > int(allowed[f.path].get("maxLen", 200)):
            raise err(422, "value_too_long", f"{f.path} is limited to {allowed[f.path].get('maxLen')} characters")
    payload = {"fields": [{"path": f.path, "value": f.value} for f in body.fields]}
    await db.run_sync(lambda s: state.transition(s, s.get_one(Project, p.id), "planning", {"reason": "edit_texts", "n": len(body.fields)}))
    await db.commit()
    job_id = await run_in_threadpool(svc.enqueue_edit, p, user, "texts", payload)
    await db.refresh(p)
    return EnqueuedOut(project=await svc.project_out(p), job_id=job_id)


@router.post("/{project_id}/asset-slots", response_model=EnqueuedOut)
async def edit_asset_slots(project_id: uuid.UUID, body: AssetSlotsIn, user: CurrentUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    _require_preview_ready(p)
    if not body.changes and not body.insert:
        raise err(422, "nothing_to_do", "give changes and/or insert")
    ready = {a.name for a in (await db.execute(select(ProjectAsset).where(ProjectAsset.project_id == p.id, ProjectAsset.status == "ready"))).scalars()}
    slots = {s["path"] for s in (p.asset_slots or [])}
    for c in body.changes:
        if c.path not in slots:
            raise err(422, "invalid_slot", f"{c.path} is not a media slot")
        if c.asset is not None and c.asset not in ready:
            raise err(422, "unknown_asset", f"asset {c.asset} is not ready")
    n_words = len(p.words or [])
    for i in body.insert:
        if i.asset not in ready:
            raise err(422, "unknown_asset", f"asset {i.asset} is not ready")
        if i.at_word >= n_words:
            raise err(422, "invalid_word", f"at_word must be < {n_words}")
    payload = {"changes": [c.model_dump() for c in body.changes], "insert": [i.model_dump() for i in body.insert]}
    await db.run_sync(lambda s: state.transition(s, s.get_one(Project, p.id), "planning", {"reason": "asset_slots", "changes": len(body.changes), "insert": len(body.insert)}))
    await db.commit()
    job_id = await run_in_threadpool(svc.enqueue_edit, p, user, "assets", payload)
    await db.refresh(p)
    return EnqueuedOut(project=await svc.project_out(p), job_id=job_id)


@router.post("/{project_id}/render", response_model=EnqueuedOut)
async def render(project_id: uuid.UUID, user: VerifiedUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    _require_preview_ready(p)
    await svc.check_concurrency(db, user)
    job_id = await svc.reserve_and_queue_render(db, user, p)
    await db.refresh(p)
    return EnqueuedOut(project=await svc.project_out(p), job_id=job_id)


@router.post("/{project_id}/retry", response_model=EnqueuedOut)
async def retry(project_id: uuid.UUID, user: VerifiedUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    if p.status != "failed":
        raise err(409, "not_failed", "only failed projects can be retried")
    await svc.check_concurrency(db, user)
    stage = p.failed_stage or "preview"
    if stage == "render":
        job_id = await svc.reserve_and_queue_render(db, user, p)
    else:
        def _tx(s):
            sp = s.get(Project, p.id)
            sp.attempts += 1
            state.transition(s, sp, "queued_transcribe", {"retry": True, "stage": stage})
        await db.run_sync(_tx)
        await db.commit()
        await db.refresh(p)
        job_id = await run_in_threadpool(svc.enqueue_preview, p, user)
        p.rq_job_id = job_id
        await db.commit()
    await db.refresh(p)
    return EnqueuedOut(project=await svc.project_out(p), job_id=job_id)


@router.get("/{project_id}/download", response_model=DownloadOut)
async def download(project_id: uuid.UUID, user: CurrentUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    if p.status != "done" or not p.output_key:
        raise err(409, "not_done", "the video is not rendered yet")
    safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in p.title).strip() or "video"
    filename = f"{safe}.mp4"
    url = await svc.presigned(p.output_key, filename)
    return DownloadOut(url=url or "", expires_in=get_settings().presign_ttl_s, filename=filename)


@router.get("/{project_id}/preview", response_model=ProjectOut)
async def preview(project_id: uuid.UUID, user: CurrentUser, db: DB):
    p = await svc.get_owned_project(db, user, project_id)
    return await svc.project_out(p)
