"""SQLAlchemy 2 models (§5.7 of the brief). Alembic migrations in apps/api/alembic are the DDL source of truth."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

JSONType = JSON().with_variant(JSONB, "postgresql")


def now() -> datetime:
    return datetime.utcnow()


class Base(DeclarativeBase):
    __mapper_args__ = {"eager_defaults": True}


STATUSES = ["created", "uploading", "queued_transcribe", "transcribing", "editing", "planning", "preview_ready", "queued_render", "rendering", "done", "failed"]
PROGRESS = {"created": 0, "uploading": 2, "queued_transcribe": 5, "transcribing": 10, "editing": 40, "planning": 50, "preview_ready": 75,
            "queued_render": 78, "rendering": 80, "done": 100, "failed": 0}
LEDGER_REASONS = ["grant", "plan_renewal", "reserve", "commit", "release", "refund", "admin"]


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    locale: Mapped[str] = mapped_column(String(8), default="en", nullable=False)
    plan: Mapped[str] = mapped_column(String(16), default="free", nullable=False)
    credits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # fast path = SUM(credit_ledger.delta)
    ls_customer_id: Mapped[str | None] = mapped_column(String(64))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    brand_kit: Mapped[BrandKit | None] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class BrandKit(Base):
    __tablename__ = "brand_kits"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    palette: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    fonts: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    logo_key: Mapped[str | None] = mapped_column(String(512))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    user: Mapped[User] = relationship(back_populates="brand_kit")


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    template: Mapped[str] = mapped_column(String(32), nullable=False)
    lang: Mapped[str | None] = mapped_column(String(16))
    size: Mapped[str] = mapped_column(String(16), default="9:16", nullable=False)
    size_w: Mapped[int] = mapped_column(Integer, nullable=False)
    size_h: Mapped[int] = mapped_column(Integer, nullable=False)
    platform: Mapped[str] = mapped_column(String(16), default="none", nullable=False)
    brief: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="created", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    input_key: Mapped[str | None] = mapped_column(String(512))
    input_kind: Mapped[str | None] = mapped_column(String(8))
    script: Mapped[str | None] = mapped_column(Text)
    plan: Mapped[dict | None] = mapped_column(JSONType)
    editable_fields: Mapped[list | None] = mapped_column(JSONType)
    asset_slots: Mapped[list | None] = mapped_column(JSONType)
    words: Mapped[list | None] = mapped_column(JSONType)
    detected_lang: Mapped[str | None] = mapped_column(String(16))
    output_key: Mapped[str | None] = mapped_column(String(512))
    preview_key: Mapped[str | None] = mapped_column(String(512))   # contact sheet
    sheet_key: Mapped[str | None] = mapped_column(String(512))     # final sheet
    duration_s: Mapped[float | None] = mapped_column(Numeric(10, 3))
    credits_reserved: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    credits_committed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    planner: Mapped[str | None] = mapped_column(String(16))
    llm_model: Mapped[str | None] = mapped_column(String(128))
    llm_tokens_in: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    llm_tokens_out: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    llm_cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0, nullable=False)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_stage: Mapped[str | None] = mapped_column(String(16))   # preview | render | edit
    rq_job_id: Mapped[str | None] = mapped_column(String(64))
    output_size: Mapped[list | None] = mapped_column(JSONType)
    qa: Mapped[dict | None] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    done_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    assets: Mapped[list[ProjectAsset]] = relationship(back_populates="project", cascade="all, delete-orphan", order_by="ProjectAsset.created_at")

    __table_args__ = (Index("ix_projects_user_created", "user_id", created_at.desc()), Index("ix_projects_status", "status"))


class ProjectAsset(Base):
    __tablename__ = "project_assets"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    kind: Mapped[str] = mapped_column(String(8), nullable=False)                  # image | clip
    key: Mapped[str] = mapped_column(String(512), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime: Mapped[str] = mapped_column(String(128), nullable=False)
    bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    duration_s: Mapped[float | None] = mapped_column(Numeric(10, 3))
    has_alpha: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str] = mapped_column(String(300), default="", nullable=False)
    description_source: Mapped[str | None] = mapped_column(String(8))            # user | ai
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)  # pending | uploaded | ready | invalid
    error: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    project: Mapped[Project] = relationship(back_populates="assets")

    @property
    def name(self) -> str:
        return "asset_" + self.id.hex[:12]


class TemplateRequest(Base):
    __tablename__ = "template_requests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    example_url: Mapped[str | None] = mapped_column(String(1024))
    file_key: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[str] = mapped_column(String(16), default="new", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class JobEvent(Base):
    __tablename__ = "job_events"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status: Mapped[str | None] = mapped_column(String(24))
    to_status: Mapped[str] = mapped_column(String(24), nullable=False)
    detail: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class CreditLedger(Base):
    __tablename__ = "credit_ledger"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(16), nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"))
    external_id: Mapped[str | None] = mapped_column(String(128), unique=True)
    note: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(24), nullable=False)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(24), nullable=False)
    external_event_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TemplateFlag(Base):
    __tablename__ = "template_flags"
    name: Mapped[str] = mapped_column(String(32), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tier_required: Mapped[str] = mapped_column(String(16), default="free", nullable=False)


class AppSetting(Base):
    __tablename__ = "app_settings"
    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(JSONType)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
