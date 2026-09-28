"""Project state machine (§5.2). Every transition writes a job_events row in the same transaction."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from .models import PROGRESS, JobEvent, Project

ALLOWED = {
    "created": {"uploading", "queued_transcribe", "failed"},
    "uploading": {"queued_transcribe", "failed"},
    "queued_transcribe": {"transcribing", "failed"},
    "transcribing": {"editing", "failed"},
    "editing": {"planning", "failed"},
    "planning": {"preview_ready", "failed"},
    "preview_ready": {"planning", "queued_render", "failed"},
    "queued_render": {"rendering", "failed", "preview_ready"},
    "rendering": {"done", "failed"},
    "done": set(),
    "failed": {"queued_transcribe", "queued_render", "planning"},   # retry
}


class IllegalTransition(Exception):
    pass


def transition(s: Session, project: Project, to: str, detail: dict | None = None, *, force: bool = False) -> JobEvent:
    frm = project.status
    if not force and to != frm and to not in ALLOWED.get(frm, set()):
        raise IllegalTransition(f"{frm} → {to} is not allowed")
    project.status = to
    project.progress = PROGRESS.get(to, project.progress)
    if to == "done":
        project.done_at = datetime.utcnow()
    if to not in ("failed",):
        project.error_code = None; project.error_message = None
    ev = JobEvent(project_id=project.id, from_status=frm, to_status=to, detail=detail or {})
    s.add(ev)
    s.flush()
    return ev


def fail(s: Session, project: Project, code: str, message: str, stage: str, detail: dict | None = None) -> JobEvent:
    project.error_code = code
    project.error_message = message[:2000]
    project.failed_stage = stage
    return transition(s, project, "failed", {"error_code": code, "message": message[:500], "stage": stage, **(detail or {})}, force=True)


def set_progress(s: Session, project: Project, progress: int, detail: dict | None = None) -> None:
    project.progress = max(project.progress, min(99, int(progress)))
    if detail:
        s.add(JobEvent(project_id=project.id, from_status=project.status, to_status=project.status, detail=detail))
    s.flush()


def progress_within(status: str, frac: float) -> int:
    """Map a 0..1 fraction inside a step onto the global 0..100 progress scale."""
    order = ["queued_transcribe", "transcribing", "editing", "planning", "preview_ready", "queued_render", "rendering", "done"]
    if status not in order:
        return PROGRESS.get(status, 0)
    a = PROGRESS[status]
    b = PROGRESS[order[order.index(status) + 1]] if order.index(status) + 1 < len(order) else 100
    return int(a + (b - a) * max(0.0, min(1.0, frac)))
