"""/health (db, redis, s3) and /metrics (Prometheus text format, computed from the database)."""
from __future__ import annotations

import time

from fastapi import APIRouter, Response
from sqlalchemy import func, select, text
from starlette.concurrency import run_in_threadpool

from ..core import queue, storage
from ..core.models import JobEvent, Project
from ..deps import DB

router = APIRouter(tags=["ops"])


@router.get("/health")
async def health(db: DB, response: Response):
    out: dict = {"status": "ok", "checks": {}}
    t0 = time.time()
    try:
        await db.execute(text("select 1")); out["checks"]["db"] = "ok"
    except Exception as e:
        out["checks"]["db"] = f"error: {e}"[:200]; out["status"] = "degraded"
    try:
        await run_in_threadpool(queue.ping); out["checks"]["redis"] = "ok"
    except Exception as e:
        out["checks"]["redis"] = f"error: {e}"[:200]; out["status"] = "degraded"
    try:
        await run_in_threadpool(storage.ping); out["checks"]["s3"] = "ok"
    except Exception as e:
        out["checks"]["s3"] = f"error: {e}"[:200]; out["status"] = "degraded"
    out["latency_ms"] = round((time.time() - t0) * 1000, 1)
    if out["status"] != "ok":
        response.status_code = 503
    return out


@router.get("/metrics")
async def metrics(db: DB):
    lines = ["# HELP vs_projects_total Projects by status", "# TYPE vs_projects_total gauge"]
    for status, n in (await db.execute(select(Project.status, func.count()).where(Project.deleted_at.is_(None)).group_by(Project.status))).all():
        lines.append(f'vs_projects_total{{status="{status}"}} {n}')
    lines += ["# HELP vs_llm_cost_usd_total Sum of LLM cost estimates", "# TYPE vs_llm_cost_usd_total counter"]
    cost = (await db.execute(select(func.coalesce(func.sum(Project.llm_cost_usd), 0)))).scalar_one()
    lines.append(f"vs_llm_cost_usd_total {float(cost):.6f}")
    # step durations: time between consecutive events per project, averaged by the step they end
    lines += ["# HELP vs_step_seconds_avg Average seconds spent in each status", "# TYPE vs_step_seconds_avg gauge"]
    q = text("""
        select from_status, avg(extract(epoch from (created_at - prev))) as secs, count(*) as n from (
          select from_status, created_at, lag(created_at) over (partition by project_id order by id) as prev from job_events
          where from_status is not null and from_status <> to_status) t where prev is not null group by from_status""")
    for st, secs, n in (await db.execute(q)).all():
        lines.append(f'vs_step_seconds_avg{{status="{st}"}} {float(secs or 0):.1f}')
        lines.append(f'vs_step_transitions_total{{status="{st}"}} {int(n)}')
    try:
        for name, n in (await run_in_threadpool(queue.queue_sizes)).items():
            lines.append(f'vs_queue_size{{queue="{name}"}} {n}')
    except Exception:
        pass
    _ = JobEvent
    return Response("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")
