"""Request/response models."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Msg(BaseModel):
    ok: bool = True
    message: str = ""


# ---- auth
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    locale: Literal["en", "ar"] = "en"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenIn(BaseModel):
    token: str


class ForgotIn(BaseModel):
    email: EmailStr


class ResetIn(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=200)


class AuthOut(BaseModel):
    user: UserOut
    csrf_token: str
    access_token: str | None = None   # also set as a cookie; returned for non-browser clients


# ---- users
class BrandKitIn(BaseModel):
    palette: dict[str, str] = {}
    fonts: dict[str, str] = {}
    logo_key: str | None = None


class BrandKitOut(BrandKitIn):
    updated_at: datetime | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    locale: str
    plan: str
    credits: int
    email_verified: bool = False
    is_admin: bool = False
    created_at: datetime


class PlanInfo(BaseModel):
    name: str
    price_usd: float = 0
    credits: int = 0
    max_res: int = 720
    watermark: bool = True
    templates: str = "basic"
    brand_kit: bool = False
    priority_queue: bool = False
    output_retention_days: int = 30


class LimitsOut(BaseModel):
    input_max_mb: int = 200
    input_max_seconds: int = 600
    assets_per_project: int = 20
    asset_image_max_mb: int = 25
    asset_clip_max_mb: int = 100
    asset_clip_max_seconds: int = 60
    concurrent_jobs: int = 1
    projects_per_hour: int = 10


class FeaturesOut(BaseModel):
    tts: bool = False
    google_oauth: bool = False
    payments_provider: str = "mock"


class MeOut(BaseModel):
    user: UserOut
    plan: PlanInfo
    brand_kit: BrandKitOut | None
    limits: LimitsOut
    features: FeaturesOut


class UpdateMeIn(BaseModel):
    locale: Literal["en", "ar"] | None = None


class DeleteMeIn(BaseModel):
    password: str


# ---- templates
class TemplateOut(BaseModel):
    name: str
    title: str
    category: str
    summary: str
    scenes: list[str]
    media_fields: list[str] = []
    needs_media: list[str] = []
    has_ar_example: bool = False
    preview: str
    enabled: bool
    tier_required: str
    available: bool


class SizeOut(BaseModel):
    id: str
    label: str
    w: int | None
    h: int | None


class LanguageOut(BaseModel):
    code: str
    name: str


class CatalogOut(BaseModel):
    templates: list[TemplateOut]
    sizes: list[SizeOut]
    platforms: list[str]
    languages: list[LanguageOut]
    limits: dict


# ---- uploads
class PresignIn(BaseModel):
    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    size: int = Field(gt=0)


class PresignOut(BaseModel):
    url: str
    fields: dict[str, str]
    key: str
    method: str = "POST"
    expires_in: int
    asset_id: uuid.UUID | None = None


# ---- projects
class ProjectCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    template: str
    input_key: str | None = None
    script: str | None = Field(default=None, max_length=8000)
    lang: str | None = Field(default=None, max_length=16)
    size: str = "9:16"
    platform: str = "none"
    brief: dict[str, Any] = {}


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    kind: str
    original_name: str
    mime: str
    bytes: int
    width: int | None
    height: int | None
    duration_s: float | None
    has_alpha: bool
    description: str
    description_source: str | None
    status: str
    error: str | None
    thumbnail_url: str | None = None


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    title: str
    template: str
    lang: str | None
    detected_lang: str | None
    size: str
    size_w: int
    size_h: int
    platform: str
    brief: dict
    status: str
    progress: int
    input_kind: str | None
    has_script: bool = False
    duration_s: float | None
    credits_reserved: int
    credits_committed: int
    credits_needed: int | None = None
    planner: str | None
    llm_model: str | None
    llm_cost_usd: float
    error_code: str | None
    error_message: str | None
    failed_stage: str | None
    attempts: int
    output_size: list | None
    created_at: datetime
    updated_at: datetime
    done_at: datetime | None
    preview_url: str | None = None
    sheet_url: str | None = None


class ProjectDetailOut(ProjectOut):
    plan: dict | None
    editable_fields: list | None
    asset_slots: list | None
    unused_assets: list[str] = []
    words: list | None
    assets: list[AssetOut] = []
    qa: dict | None


class ProjectListOut(BaseModel):
    items: list[ProjectOut]
    total: int


class TextEdit(BaseModel):
    path: str
    value: str = Field(max_length=500)


class TextsIn(BaseModel):
    fields: list[TextEdit] = Field(min_length=1, max_length=200)


class AssetRegisterIn(BaseModel):
    asset_id: uuid.UUID
    description: str | None = Field(default=None, max_length=300)


class AssetPatchIn(BaseModel):
    description: str = Field(max_length=300)


class SlotChange(BaseModel):
    path: str
    asset: str | None


class SlotInsert(BaseModel):
    asset: str
    at_word: int = Field(ge=0)
    dur: float = Field(default=2.0, ge=1.5, le=15)


class AssetSlotsIn(BaseModel):
    changes: list[SlotChange] = []
    insert: list[SlotInsert] = []


class TemplateRequestIn(BaseModel):
    description: str = Field(min_length=10, max_length=4000)
    example_url: str | None = Field(default=None, max_length=1024)
    file_key: str | None = None


class DownloadOut(BaseModel):
    url: str
    expires_in: int
    filename: str


class EnqueuedOut(BaseModel):
    project: ProjectOut
    job_id: str | None = None


# ---- billing
class PlanOut(BaseModel):
    name: str
    price_usd: float
    credits: int
    max_res: int
    watermark: bool
    templates: str
    brand_kit: bool = False
    priority_queue: bool = False


class CheckoutIn(BaseModel):
    plan: Literal["starter", "pro", "agency"]


class CheckoutOut(BaseModel):
    url: str


class MockSubscribeIn(BaseModel):
    plan: Literal["free", "starter", "pro", "agency"]


# ---- admin
class LLMSettingsOut(BaseModel):
    settings: dict
    defaults: dict
    providers: dict


class LLMSettingsIn(BaseModel):
    planner_model: str | None = None
    fast_model: str | None = None
    vision_model: str | None = None
    free_tier_model: str | None = None
    fallback_chain: list[str] | None = None


class GrantCreditsIn(BaseModel):
    email: EmailStr | None = None
    user_id: uuid.UUID | None = None
    credits: int = Field(ge=-1000, le=100000)
    note: str | None = Field(default=None, max_length=300)


class ToggleTemplateIn(BaseModel):
    name: str
    enabled: bool
    tier_required: Literal["free", "starter", "pro", "agency"] | None = None
