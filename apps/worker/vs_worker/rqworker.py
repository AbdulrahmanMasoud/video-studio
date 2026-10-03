"""Worker entrypoint: `python -m vs_worker.rqworker` runs an RQ worker on priority, transcribe, plan, render."""
from __future__ import annotations

import logging
import os
import sys

from redis import Redis
from rq import Queue, Worker
from vs_api.core.logsetup import setup_logging
from vs_api.core.queue import QUEUES


def main() -> int:
    setup_logging(os.environ.get("LOG_LEVEL", "info"))
    if os.environ.get("SENTRY_DSN"):
        try:
            import sentry_sdk
            from sentry_sdk.integrations.rq import RqIntegration
            sentry_sdk.init(dsn=os.environ["SENTRY_DSN"], environment=os.environ.get("APP_ENV", "dev"), send_default_pii=False, integrations=[RqIntegration()])
        except Exception as e:
            logging.getLogger("vs_worker").warning("sentry init failed: %s", e)
    url = os.environ.get("REDIS_URL", "redis://redis:6379/0")
    conn = Redis.from_url(url)
    queues = [Queue(q, connection=conn) for q in (sys.argv[1:] or QUEUES)]
    logging.getLogger("vs_worker").info("worker starting on %s", [q.name for q in queues])
    try:
        from .tasks import schedule_cleanup
        schedule_cleanup(delay_s=int(os.environ.get("CLEANUP_FIRST_DELAY_S", "120")))
    except Exception as e:  # scheduling must never prevent the worker from starting
        logging.getLogger("vs_worker").warning("cleanup scheduling failed: %s", e)
    Worker(queues, connection=conn).work(with_scheduler=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
