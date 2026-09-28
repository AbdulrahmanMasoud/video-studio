"""JSON logging shared by the API and the worker (request_id / job_id fields when present)."""
from __future__ import annotations

import json
import logging
import sys
import time


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        d = {"ts": round(time.time(), 3), "level": record.levelname.lower(), "logger": record.name, "msg": record.getMessage()}
        for k in ("request_id", "job_id", "project_id", "path", "status", "ms", "user_id"):
            if hasattr(record, k):
                d[k] = getattr(record, k)
        if record.exc_info:
            d["exc"] = self.formatException(record.exc_info)[-2000:]
        return json.dumps(d, ensure_ascii=False)


def setup_logging(level: str = "info") -> None:
    h = logging.StreamHandler(sys.stdout)
    h.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [h]
    root.setLevel(level.upper())
    logging.getLogger("uvicorn.access").disabled = True
    for noisy in ("httpx", "httpcore", "botocore", "boto3", "urllib3", "LiteLLM"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
