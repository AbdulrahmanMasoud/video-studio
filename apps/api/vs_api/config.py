"""Settings from environment variables (documented in .env.example)."""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(os.environ.get("VS_REPO_ROOT", Path(__file__).resolve().parents[3]))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    app_name: str = "VideoStudio"
    app_env: str = "dev"
    log_level: str = "info"
    secret_key: str = "dev-secret-change-me"
    admin_api_key: str = "change-me-admin-key"
    web_origin: str = "http://localhost:3000"
    api_base_url: str = "http://localhost:8000"
    cookie_secure: bool = False

    database_url: str = "postgresql+asyncpg://videostudio:videostudio@postgres:5432/videostudio"
    database_url_sync: str = "postgresql+psycopg://videostudio:videostudio@postgres:5432/videostudio"
    database_url_test_sync: str = "postgresql+psycopg://videostudio:videostudio@postgres:5432/videostudio_test"
    redis_url: str = "redis://redis:6379/0"

    job_timeout_transcribe_s: int = 900
    job_timeout_plan_s: int = 300
    job_timeout_render_s: int = 1800

    s3_endpoint_url: str = "http://minio:9000"
    s3_public_endpoint_url: str = "http://localhost:9000"
    s3_region: str = "us-east-1"
    s3_bucket: str = "videos"
    s3_access_key: str = "videostudio"
    s3_secret_key: str = "videostudio-secret"
    s3_force_path_style: bool = True
    presign_ttl_s: int = 900                       # ≤ 15 min (brief §5.10)

    email_provider: str = "smtp"
    smtp_host: str = "mailpit"
    smtp_port: int = 1025
    email_from: str = "VideoStudio <no-reply@videostudio.local>"
    resend_api_key: str = ""

    payments_provider: str = "mock"

    whisper_model: str = "small"
    worker_scratch_dir: str = "/jobs"
    watermark_path: str = str(REPO_ROOT / "packages/shared/assets/watermark.png")
    tts_enabled: bool = False
    tts_provider: str = "none"
    planner_mode: str = "llm"

    rate_limits_enabled: bool = True
    google_oauth_enabled: bool = False
    sentry_dsn: str = ""

    access_token_ttl_s: int = 15 * 60
    refresh_token_ttl_s: int = 30 * 24 * 3600
    email_token_ttl_s: int = 24 * 3600

    plans_yaml: Path = Field(default=REPO_ROOT / "packages/shared/plans.yaml")
    catalog_json: Path = Field(default=REPO_ROOT / "packages/shared/templates.json")
    engine_dir: Path = Field(default=REPO_ROOT / "engine")
    previews_dir: Path = Field(default=REPO_ROOT / "docs/previews")

    @property
    def is_prod(self) -> bool:
        return self.app_env == "prod"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
