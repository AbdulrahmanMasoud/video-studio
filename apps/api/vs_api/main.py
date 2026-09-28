"""FastAPI application factory."""
from __future__ import annotations

import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .config import get_settings
from .core.logsetup import setup_logging
from .ratelimit import limiter
from .routers import admin, assets, auth, billing, health, me, projects, template_requests, templates, uploads

log = logging.getLogger("vs_api")


def create_app() -> FastAPI:
    s = get_settings()
    setup_logging(s.log_level)
    app = FastAPI(title=f"{s.app_name} API", version="0.1.0", docs_url="/docs" if not s.is_prod else None, redoc_url=None)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(CORSMiddleware, allow_origins=[s.web_origin], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
                       expose_headers=["X-Request-Id"])

    @app.middleware("http")
    async def request_id_and_log(request: Request, call_next):
        rid = request.headers.get("X-Request-Id") or uuid.uuid4().hex[:16]
        request.state.request_id = rid
        t0 = time.time()
        try:
            response = await call_next(request)
        except Exception:
            log.exception("unhandled error", extra={"request_id": rid, "path": request.url.path})
            raise
        response.headers["X-Request-Id"] = rid
        if request.url.path not in ("/health", "/metrics"):
            log.info("request", extra={"request_id": rid, "path": f"{request.method} {request.url.path}", "status": response.status_code,
                                       "ms": round((time.time() - t0) * 1000, 1)})
        return response

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException):
        detail = exc.detail if isinstance(exc.detail, dict) else {"error_code": "http_error", "message": str(exc.detail)}
        return JSONResponse(status_code=exc.status_code, content=detail, headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=422, content={"error_code": "validation_error", "message": "invalid request", "errors": exc.errors()})

    for r in (auth.router, me.router, templates.router, uploads.router, projects.router, assets.router, template_requests.router, billing.router,
              admin.router, health.router):
        app.include_router(r)
    if s.previews_dir.exists():
        app.mount("/previews", StaticFiles(directory=str(s.previews_dir)), name="previews")
    return app


app = create_app()
