"""Job specification and results. The API builds a JobSpec from the project row; the worker runs it."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class AssetSpec(BaseModel):
    name: str = Field(pattern=r"^[A-Za-z0-9_\-]{1,64}$")
    path: Path
    kind: Literal["image", "clip"] | None = None
    description: str = ""
    fit: Literal["cover", "contain"] | None = None
    start: float = 0.0
    duration: float | None = None
    keep_audio: bool = False


class BrandKit(BaseModel):
    palette: dict[str, str] = {}
    fonts: dict[str, str] = {}
    logo: Path | None = None


class RenderOptions(BaseModel):
    draft: bool = False
    workers: int | None = None
    watermark: Path | None = None
    watermark_pos: Literal["br", "bl", "tr", "tl", "center"] = "br"
    watermark_opacity: float = 0.6
    max_height: int | None = None           # short-side cap (720 for the free plan)
    no_music: bool = False


class Timeouts(BaseModel):
    transcribe: float = 900
    edit: float = 300
    assets: float = 300
    plan: float = 300
    stills: float = 180
    render: float = 1800
    finalize: float = 600


class JobSpec(BaseModel):
    job_id: str
    template: str
    size: str = "9:16"
    lang: str | None = None                 # None: autodetect from transcription
    platform: str = "none"
    input_path: Path | None = None          # local file (already downloaded)
    script: str | None = None               # text for TTS when there is no recording
    tts_provider: str | None = None
    brief: dict = {}
    brand: BrandKit | None = None
    assets: list[AssetSpec] = []
    captions: str | None = None
    whisper_model: str = "small"
    duration_limit_s: float = 600
    pace: Literal["tight", "natural", "relaxed", "none"] = "tight"
    tier: Literal["free", "paid"] = "paid"      # picks the planner model (PLANNER_MODEL_FREE / PAID)
    llm_edit_decisions: bool = True             # let the fast model propose --drop ranges
    render: RenderOptions = RenderOptions()
    timeouts: Timeouts = Timeouts()
    fps: int = 30


class StepEvent(BaseModel):
    step: str
    status: Literal["started", "progress", "done", "failed"]
    progress: float = 0.0                   # 0..1 within the step
    message: str = ""
    error_code: str | None = None


class PreviewResult(BaseModel):
    plan: dict
    contact_sheet: Path
    transcript_edit: str
    words: list[dict]
    detected_lang: str | None
    duration_s: float
    planner: str
    warnings: list[str] = []
    asset_index: list[dict] = []
    editable_fields: list[dict] = []
    asset_slots: list[dict] = []
    unused_assets: list[str] = []
    llm: dict = {}


class RenderResult(BaseModel):
    final_mp4: Path
    final_sheet: Path | None
    qa_report: dict
    duration_s: float
    output_size: tuple[int, int]
    warnings: list[str] = []
