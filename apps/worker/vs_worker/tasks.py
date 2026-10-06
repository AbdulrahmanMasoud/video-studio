"""RQ job functions. They own the project lifecycle on the worker side: download inputs, run the Pipeline, upload outputs,
write status transitions and job_events, reserve/commit/release credits.

Idempotent: every job first checks the project's status and returns when the work is already done. Transient failures
(timeouts, crashes) raise so RQ retries once; user errors mark the project failed and return normally.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Literal, cast

from sqlalchemy import select
from sqlalchemy.orm import Session
from vs_api.config import get_settings
from vs_api.core import credits, email, state, storage
from vs_api.core.db import sync_session_factory
from vs_api.core.models import AppSetting, BrandKit, Project, ProjectAsset, User

from .errors import PipelineError
from .pipeline import Pipeline, Planner
from .planner.llm_planner import make_planner
from .spec import AssetSpec, JobSpec, RenderOptions, StepEvent, Timeouts
from .spec import BrandKit as SpecBrandKit

log = logging.getLogger("vs_worker.tasks")
STEP_STATUS = {"init": "transcribing", "tts": "transcribing", "transcribe": "transcribing", "edit": "editing", "assets": "editing", "plan": "planning",
               "stills": "planning", "render": "rendering", "finalize": "rendering"}
STEP_FRAC = {"init": 0.0, "tts": 0.05, "transcribe": 0.1, "edit": 0.0, "assets": 0.6, "plan": 0.0, "stills": 0.8, "render": 0.0, "finalize": 0.85}


def scratch_root() -> Path:
    return Path(os.environ.get("WORKER_SCRATCH_DIR") or get_settings().worker_scratch_dir)


def _session() -> Session:
    return sync_session_factory()()


def _project(s: Session, project_id) -> Project:
    p = s.get(Project, project_id)
    if p is None:
        raise PipelineError("gone", f"project {project_id} not found", transient=False)
    return p


def _user(s: Session, user_id) -> User:
    u = s.get(User, user_id)
    if u is None:
        raise PipelineError("gone", f"user {user_id} not found", transient=False)
    return u


def _llm_overrides(s: Session) -> dict:
    rows: list[AppSetting] = list(s.execute(select(AppSetting).where(AppSetting.key.like("llm.%"))).scalars())
    return {r.key: r.value for r in rows}


def _asset_specs(s: Session, p: Project, job_dir: Path) -> list[AssetSpec]:
    q = select(ProjectAsset).where(ProjectAsset.project_id == p.id, ProjectAsset.status.in_(("uploaded", "ready", "invalid")))
    rows: list[ProjectAsset] = list(s.execute(q).scalars().all())
    specs: list[AssetSpec] = []
    for a in rows:
        dst = job_dir / "assets_in" / f"{a.name}{Path(a.key).suffix}"
        if not dst.exists():
            try:
                storage.download(a.key, dst)
            except Exception as e:
                a.status, a.error = "invalid", f"download failed: {e}"[:300]
                continue
        specs.append(AssetSpec(name=a.name, path=dst, kind=a.kind, description=a.description or ""))
    s.flush()
    return specs


def build_spec(s: Session, p: Project, job_dir: Path, *, tier: Literal["free", "paid"]) -> JobSpec:
    cfg = get_settings()
    user = _user(s, p.user_id)
    bk = s.execute(select(BrandKit).where(BrandKit.user_id == p.user_id)).scalar_one_or_none()
    from vs_api.core import plans
    rules = plans.render_rules(user.plan)
    input_path: Path | None = None
    if p.input_key:
        input_path = job_dir / "input" / Path(p.input_key).name
        if not input_path.exists():
            storage.download(p.input_key, input_path)
    brand = SpecBrandKit(palette=bk.palette or {}, fonts=bk.fonts or {}) if bk and rules["brand_kit"] else None
    return JobSpec(job_id="job", template=p.template, size=p.size if p.size in ("9:16", "1:1", "4:5", "16:9") else f"{p.size_w}x{p.size_h}",
                   lang=p.lang, platform=p.platform, input_path=input_path, script=p.script if not p.input_key else None,
                   tts_provider=cfg.tts_provider if cfg.tts_provider != "none" else None, brief=p.brief or {}, brand=brand,
                   assets=_asset_specs(s, p, job_dir), whisper_model=cfg.whisper_model, duration_limit_s=float(plans.limits().get("input_max_seconds", 600)),
                   tier=tier,
                   render=RenderOptions(draft=os.environ.get("RENDER_DRAFT", "0") in ("1", "true"), watermark=Path(cfg.watermark_path) if rules["watermark"] else None,
                                        max_height=rules["max_res"], workers=int(os.environ.get("RENDER_WORKERS", "2"))),
                   timeouts=Timeouts(transcribe=cfg.job_timeout_transcribe_s, plan=cfg.job_timeout_plan_s, render=cfg.job_timeout_render_s))


class Progress:
    """Throttled progress writer: status transitions per step, progress % from step fractions."""

    def __init__(self, project_id, stage: str):
        self.project_id, self.stage, self.last = project_id, stage, 0.0
        self.step_status: str | None = None

    def __call__(self, ev: StepEvent):
        if ev.status == "started":
            self._transition(STEP_STATUS.get(ev.step))
        elif ev.status == "progress" and time.time() - self.last > 2:
            self.last = time.time()
            with _session() as s:
                p = s.get(Project, self.project_id)
                if p is not None and p.status == STEP_STATUS.get(ev.step):
                    state.set_progress(s, p, state.progress_within(p.status, STEP_FRAC.get(ev.step, 0) + ev.progress * (1 - STEP_FRAC.get(ev.step, 0))))
                    s.commit()

    def _transition(self, status: str | None):
        if not status or status == self.step_status:
            return
        with _session() as s:
            p = s.get(Project, self.project_id)
            if p is not None and p.status != status and status in state.ALLOWED.get(p.status, set()):
                state.transition(s, p, status, {"stage": self.stage})
                s.commit()
                self.step_status = status


def _store_preview(s: Session, p: Project, preview, job_dir: Path) -> None:
    uid = p.user_id
    if preview.contact_sheet.exists():
        p.preview_key = storage.upload(preview.contact_sheet, storage.output_key(uid, p.id, "contact_sheet.jpg"), "image/jpeg")
    storage.put_bytes(json.dumps(preview.plan, ensure_ascii=False).encode(), storage.output_key(uid, p.id, "plan.json"), "application/json")
    p.plan, p.editable_fields, p.asset_slots, p.words = preview.plan, preview.editable_fields, preview.asset_slots, preview.words
    p.detected_lang = preview.detected_lang
    p.duration_s = preview.duration_s
    p.planner = preview.planner
    llm = preview.llm or {}
    p.llm_model = llm.get("model"); p.llm_tokens_in = int(llm.get("tokens_in", 0)); p.llm_tokens_out = int(llm.get("tokens_out", 0))
    p.llm_cost_usd = float(llm.get("cost_usd", 0))
    by: dict[str, dict] = {r["name"]: r for r in preview.asset_index}
    a: ProjectAsset
    for a in s.execute(select(ProjectAsset).where(ProjectAsset.project_id == p.id)).scalars():
        rec = by.get(a.name)
        if not rec:
            continue
        if rec.get("error"):
            a.status, a.error = "invalid", str(rec["error"])[:300]
        else:
            a.status, a.error = "ready", None
            a.width, a.height, a.has_alpha = rec.get("width"), rec.get("height"), bool(rec.get("alpha"))
            a.duration_s = rec.get("duration")
            if rec.get("description") and not a.description:
                a.description, a.description_source = rec["description"][:300], rec.get("description_source", "ai")


def _fail(project_id, e: PipelineError, stage: str) -> None:
    with _session() as s:
        p = s.get(Project, project_id)
        if p is None:
            return
        if stage == "render":
            credits.release(s, p)
        state.fail(s, p, e.code, e.message, stage, {"transient": e.transient, "step": e.step})
        s.commit()
        if stage == "render":
            u = _user(s, p.user_id)
            email.send(u.email, "render_failed", u.locale, title=p.title, code=e.code, link=f"{get_settings().web_origin}/app/projects/{p.id}")


def _pipeline(s: Session, p: Project, job_dir: Path, stage: str) -> Pipeline:
    user = _user(s, p.user_id)
    tier: Literal["free", "paid"] = "free" if user.plan == "free" else "paid"
    spec = build_spec(s, p, job_dir, tier=tier)
    planner = cast(Planner, make_planner(get_settings().planner_mode, tier=tier, overrides=_llm_overrides(s)))
    return Pipeline(spec, job_dir.parent, on_event=Progress(p.id, stage), planner=planner,
                    offline_render=os.environ.get("VT_OFFLINE_RENDER", "1") not in ("0", "false"))


def _job_dir(project_id) -> Path:
    return scratch_root() / str(project_id) / "job"


# ------------------------------------------------------------------ jobs
def preview_job(project_id: str) -> str:
    """queued_transcribe → transcribing → editing → planning → preview_ready (or failed)."""
    job_dir = _job_dir(project_id)
    with _session() as s:
        p = s.get(Project, project_id)
        if not p or p.deleted_at:
            return "gone"
        if p.status not in ("queued_transcribe", "transcribing", "editing", "planning"):
            return f"skip:{p.status}"
        if p.status != "queued_transcribe":  # retry after a crash mid-way: restart the stage cleanly
            state.transition(s, p, "queued_transcribe", {"restart": True}, force=True); s.commit()
        try:
            shutil.rmtree(job_dir, ignore_errors=True)
            pipe = _pipeline(s, p, job_dir, "preview")
            s.commit()
        except Exception as e:
            _fail(project_id, PipelineError("worker_crash", f"setup failed: {e}", step="init", transient=True), "preview")
            raise
    try:
        preview = pipe.prepare_preview()
    except PipelineError as e:
        _fail(project_id, e, "preview")
        if e.transient:
            raise
        return f"failed:{e.code}"
    with _session() as s:
        p = _project(s, project_id)
        _store_preview(s, p, preview, job_dir)
        if p.status != "preview_ready":
            state.transition(s, p, "preview_ready", {"planner": preview.planner, "warnings": preview.warnings[:10], "duration_s": preview.duration_s}, force=True)
        s.commit()
    return "preview_ready"


def _ensure_job_dir(s: Session, p: Project, job_dir: Path) -> Pipeline:
    """The scratch folder normally survives on the jobs volume; rebuild it from the stored plan when it is gone."""
    pipe = _pipeline(s, p, job_dir, "render")
    if not (job_dir / "plan.json").exists() or not (job_dir / "words_edit.json").exists():
        log.warning("job folder missing for %s: rebuilding from inputs", p.id)
        shutil.rmtree(job_dir, ignore_errors=True)
        pipe.planner = _StoredPlan(p.plan or {})
        pipe.prepare_preview()
    return pipe


class _StoredPlan:
    name = "stored"

    def __init__(self, plan: dict):
        self._plan = plan

    def plan(self, ctx) -> dict:
        return dict(self._plan)


def render_job(project_id: str) -> str:
    """queued_render → rendering → done (credits committed) or failed (credits released)."""
    job_dir = _job_dir(project_id)
    with _session() as s:
        p = s.get(Project, project_id)
        if not p or p.deleted_at:
            return "gone"
        if p.status == "done":
            return "skip:done"
        if p.status not in ("queued_render", "rendering"):
            return f"skip:{p.status}"
        if p.status == "rendering":
            state.transition(s, p, "queued_render", {"restart": True}, force=True); s.commit()
        try:
            pipe = _ensure_job_dir(s, p, job_dir)
            s.commit()
        except PipelineError as e:
            _fail(project_id, e, "render")
            if e.transient:
                raise
            return f"failed:{e.code}"
    try:
        result = pipe.render()
    except PipelineError as e:
        _fail(project_id, e, "render")
        if e.transient:
            raise
        return f"failed:{e.code}"
    with _session() as s:
        p = _project(s, project_id)
        uid = p.user_id
        p.output_key = storage.upload(result.final_mp4, storage.output_key(uid, p.id, "final.mp4"), "video/mp4")
        if result.final_sheet and result.final_sheet.exists():
            p.sheet_key = storage.upload(result.final_sheet, storage.output_key(uid, p.id, "final_sheet.jpg"), "image/jpeg")
        p.qa = result.qa_report
        p.output_size = list(result.output_size)
        p.duration_s = result.duration_s or p.duration_s
        credits.commit(s, p)
        state.transition(s, p, "done", {"output_size": list(result.output_size), "qa_issues": result.qa_report.get("issues", []), "warnings": result.warnings[:10]},
                         force=True)
        s.commit()
        u = _user(s, uid)
        email.send(u.email, "render_done", u.locale, title=p.title, link=f"{get_settings().web_origin}/app/projects/{p.id}")
    shutil.rmtree(job_dir.parent, ignore_errors=True)
    return "done"


def edit_job(project_id: str, kind: str, payload: dict) -> str:
    """planning (edit_texts / asset_slots) → preview_ready. Runs stills again; on a bad edit the previous plan is kept."""
    job_dir = _job_dir(project_id)
    with _session() as s:
        p = s.get(Project, project_id)
        if not p or p.deleted_at:
            return "gone"
        if p.status != "planning":
            return f"skip:{p.status}"
        try:
            pipe = _ensure_job_dir(s, p, job_dir)
            if kind == "assets":
                _register_new_assets(s, p, pipe)
            s.commit()
        except PipelineError as e:
            _fail(project_id, e, "edit")
            if e.transient:
                raise
            return f"failed:{e.code}"
    try:
        if kind == "texts":
            preview = pipe.apply_texts(payload.get("fields", []))
        else:
            preview = pipe.apply_assets(payload.get("changes", []), payload.get("insert", []))
    except PipelineError as e:
        with _session() as s:  # keep the last good plan; surface the reason as an event
            p = _project(s, project_id)
            state.transition(s, p, "preview_ready", {"edit": kind, "rejected": e.message[:300], "error_code": e.code}, force=True)
            s.commit()
        if e.transient:
            raise
        return f"rejected:{e.code}"
    with _session() as s:
        p = _project(s, project_id)
        _store_preview(s, p, preview, job_dir)
        state.transition(s, p, "preview_ready", {"edit": kind}, force=True)
        s.commit()
    return "preview_ready"


def _register_new_assets(s: Session, p: Project, pipe: Pipeline) -> None:
    """Assets uploaded after the preview: register them in the job so they can be inserted/swapped."""
    known = set(pipe.job_json.get("media", {}))
    specs = [a for a in _asset_specs(s, p, pipe.job_dir) if a.name not in known]
    if not specs:
        return
    pipe.spec.assets = specs
    pipe._run_step("assets", pipe._assets)
    by: dict[str, dict] = {r["name"]: r for r in pipe._read_json("media/index.json", [])}
    a: ProjectAsset
    for a in s.execute(select(ProjectAsset).where(ProjectAsset.project_id == p.id)).scalars():
        rec = by.get(a.name)
        if rec is None:
            continue
        if rec.get("error"):
            a.status, a.error = "invalid", str(rec["error"])[:300]
        elif a.status != "ready":
            a.status, a.error = "ready", None
            a.width, a.height, a.has_alpha, a.duration_s = rec.get("width"), rec.get("height"), bool(rec.get("alpha")), rec.get("duration")


# ------------------------------------------------------------------ scheduled cleanup (§5.3 lifecycle)
CLEANUP_JOB_ID = "cleanup-hourly"


def cleanup_job() -> dict:
    """Inputs are deleted 7 days after `done`; outputs after the plan's retention (30 days free, 180 paid); stale scratch
    folders and never-uploaded assets are removed. Re-schedules itself every hour (see schedule_cleanup)."""
    from datetime import datetime, timedelta

    from vs_api.core import plans
    from vs_api.core.models import ProjectAsset

    now = datetime.utcnow()
    stats = {"inputs": 0, "outputs": 0, "assets": 0, "scratch": 0}
    with _session() as s:
        done: list[Project] = list(s.execute(select(Project).where(Project.status == "done", Project.deleted_at.is_(None))).scalars().all())
        for p in done:
            u = s.get(User, p.user_id)
            retention = plans.render_rules(u.plan if u else "free")["output_retention_days"]
            age = now - (p.done_at.replace(tzinfo=None) if p.done_at else p.updated_at.replace(tzinfo=None))
            if p.input_key and age > timedelta(days=int(plans.limits().get("input_retention_days", 7))):
                try:
                    storage.delete(p.input_key); p.input_key = None; stats["inputs"] += 1
                except Exception as e:
                    log.warning("cleanup input %s: %s", p.id, e)
            if p.output_key and age > timedelta(days=retention):
                try:
                    storage.delete_prefix(f"outputs/{p.user_id}/{p.id}/"); p.output_key = None; p.sheet_key = None; p.preview_key = None
                    state.transition(s, p, "done", {"expired": True, "retention_days": retention}, force=True); stats["outputs"] += 1
                except Exception as e:
                    log.warning("cleanup outputs %s: %s", p.id, e)
        stale: list[ProjectAsset] = list(s.execute(select(ProjectAsset).where(ProjectAsset.status == "pending")).scalars().all())
        for a in stale:
            if now - a.created_at.replace(tzinfo=None) > timedelta(days=1):
                s.delete(a); stats["assets"] += 1
        s.commit()
    root = scratch_root()
    if root.exists():
        for d in root.iterdir():
            try:
                if d.is_dir() and now.timestamp() - d.stat().st_mtime > 2 * 86400:
                    shutil.rmtree(d, ignore_errors=True); stats["scratch"] += 1
            except OSError:
                pass
    log.info("cleanup done", extra={"job_id": CLEANUP_JOB_ID, **{}})
    schedule_cleanup()
    return stats


def schedule_cleanup(delay_s: int = 3600) -> None:
    """Enqueue the next cleanup run (idempotent: one scheduled job id)."""
    from datetime import timedelta

    from rq.job import Job
    from vs_api.core import queue as q
    try:
        existing = Job.fetch(CLEANUP_JOB_ID, connection=q.conn())
        if existing.get_status() in ("queued", "scheduled", "started", "deferred"):
            return
    except Exception:
        pass
    q.queue("plan").enqueue_in(timedelta(seconds=delay_s), "vs_worker.tasks.cleanup_job", job_id=CLEANUP_JOB_ID, job_timeout=600, result_ttl=600)
