"""RQ queues: transcribe, plan, render, priority (agency). Jobs are retried once (transient failures only) and time-limited."""
from __future__ import annotations

from functools import lru_cache

import redis
from rq import Queue, Retry
from rq.job import Job

from ..config import get_settings

QUEUES = ["priority", "transcribe", "plan", "render"]


@lru_cache(maxsize=1)
def conn() -> redis.Redis:
    return redis.Redis.from_url(get_settings().redis_url)


def queue(name: str) -> Queue:
    return Queue(name, connection=conn())


def enqueue(kind: str, func: str, *args, priority: bool = False, timeout: int, job_id: str | None = None, **kwargs) -> Job:
    """kind: transcribe | plan | render; func: dotted path in the worker (e.g. 'vs_worker.tasks.preview_job')."""
    q = queue("priority" if priority else kind)
    return q.enqueue(func, *args, job_timeout=timeout, retry=Retry(max=1, interval=10), job_id=job_id, result_ttl=3600, failure_ttl=7 * 24 * 3600,
                     description=f"{kind} {args[0] if args else ''}", **kwargs)


def job_status(job_id: str) -> str | None:
    try:
        return Job.fetch(job_id, connection=conn()).get_status()
    except Exception:
        return None


def cancel(job_id: str) -> None:
    try:
        Job.fetch(job_id, connection=conn()).cancel()
    except Exception:
        pass


def ping() -> bool:
    return bool(conn().ping())


def queue_sizes() -> dict[str, int]:
    return {q: queue(q).count for q in QUEUES}
