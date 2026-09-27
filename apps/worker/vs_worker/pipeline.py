"""Run a job end to end from a JobSpec with the engine CLI. No LLM is involved here: the planner is injected.

    pipe = Pipeline(spec, workdir, on_event=print_event)
    preview = pipe.prepare_preview()      # init → (tts) → transcribe → analyze → edit → media → assets → plan → stills
    ...user edits texts / swaps assets → pipe.apply_plan(new_plan)
    result = pipe.render()                # render → sfx → music → mix → mux (watermark/max-height) → qa
    pipe.cleanup()

Every step is safe to re-run on the same job folder (the engine overwrites its outputs), so a retry after a
crash resumes by simply running the stage again.
"""
from __future__ import annotations

import json
import re
import shutil
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol

from .engine import ENGINE_DIR, EngineEvent, EngineRunner
from .errors import PipelineError
from .planner import fallback
from .spec import JobSpec, PreviewResult, RenderResult, StepEvent


@dataclass
class PlanContext:
    template: str
    lang: str
    words: list[dict]
    transcript_edit: str
    brief: dict
    media: dict                      # job.json media entries
    asset_index: list[dict]          # media/index.json
    template_dir: Path
    size: tuple[int, int]
    platform: str
    brand: dict = field(default_factory=dict)
    duration_hint: float | None = None


class Planner(Protocol):
    name: str

    def plan(self, ctx: PlanContext) -> dict: ...


class FallbackPlanner:
    name = fallback.NAME

    def plan(self, ctx: PlanContext) -> dict:
        return fallback.plan(ctx.template, ctx.words, ctx.lang, brief=ctx.brief, media=ctx.media, duration=ctx.duration_hint)


class Pipeline:
    def __init__(self, spec: JobSpec, workdir: Path, *, on_event: Callable[[StepEvent], None] | None = None, planner: Planner | None = None,
                 offline_render: bool = True, engine_env: dict | None = None):
        self.spec = spec
        self.workdir = Path(workdir)
        self.job_dir = self.workdir / spec.job_id
        self.job_dir.mkdir(parents=True, exist_ok=True)
        self.on_event = on_event
        self.planner = planner or FallbackPlanner()
        self.offline_render = offline_render
        self._step = "init"
        self.engine = EngineRunner(self.job_dir, env=engine_env, on_event=self._engine_event)
        self.warnings: list[str] = []
        self.timings: dict[str, float] = {}

    # ------------------------------------------------------------------ events
    def _emit(self, status: Literal["started", "progress", "done", "failed"], progress: float = 0.0, message: str = "", error_code: str | None = None):
        if self.on_event:
            try:
                self.on_event(StepEvent(step=self._step, status=status, progress=progress, message=message, error_code=error_code))
            except Exception:
                pass

    def _engine_event(self, ev: EngineEvent):
        if ev.level == "progress" and ev.progress is not None:
            self._emit("progress", ev.progress, ev.msg)
        elif ev.level == "warning":
            self.warnings.append(ev.msg)

    def _run_step(self, name: str, fn: Callable[[], object]):
        self._step = name
        self._emit("started")
        t0 = time.time()
        try:
            out = fn()
        except PipelineError as e:
            e.step = e.step or name
            self._emit("failed", 0.0, e.message, e.code)
            raise
        except Exception as e:  # unexpected: transient by default so the queue retries once
            err = PipelineError("worker_crash", f"{type(e).__name__}: {e}", step=name, transient=True)
            self._emit("failed", 0.0, err.message, err.code)
            raise err from e
        self.timings[name] = round(time.time() - t0, 2)
        self._emit("done", 1.0)
        return out

    # ------------------------------------------------------------------ job.json helpers
    @property
    def job_json(self) -> dict:
        p = self.job_dir / "job.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

    def _patch_job(self, **kv):
        p = self.job_dir / "job.json"
        d = self.job_json
        d.update(kv)
        p.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")

    def _read_json(self, name, default=None):
        p = self.job_dir / name
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default

    @property
    def template_dir(self) -> Path:
        return ENGINE_DIR / self.spec.template

    # ------------------------------------------------------------------ stages
    def prepare_preview(self) -> PreviewResult:
        s = self.spec
        if not s.input_path and not s.script:
            raise PipelineError("input_missing", "a job needs an input recording or a script", step="init", transient=False)
        self._run_step("init", self._init)
        if not s.input_path:
            self._run_step("tts", self._tts)
        self._run_step("transcribe", self._transcribe)
        self._run_step("edit", self._edit)
        if s.assets:
            self._run_step("assets", self._assets)
        self._run_step("plan", self._plan)
        self._run_step("stills", self._stills)
        return self._preview_result()

    def apply_plan(self, plan: dict) -> PreviewResult:
        """Write an edited plan (texts, asset slots) and re-run stills as the validator."""
        (self.job_dir / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        self._run_step("stills", self._stills)
        return self._preview_result()

    def render(self) -> RenderResult:
        if not (self.job_dir / "plan.json").exists():
            raise PipelineError("plan_missing", "render called before a plan exists", step="render", transient=False)
        self._run_step("render", self._render)
        self._run_step("finalize", self._finalize)
        rep = self._read_json("qa/report.json", {})
        jd = self.job_json
        sheet = self.job_dir / "qa/final_sheet.jpg"
        return RenderResult(final_mp4=Path(jd["final"]), final_sheet=sheet if sheet.exists() else None, qa_report=rep,
                            duration_s=float(rep.get("duration") or jd.get("duration") or 0), output_size=tuple(jd.get("output_size") or self._size()),
                            warnings=list(dict.fromkeys(self.warnings)))

    def run(self) -> tuple[PreviewResult, RenderResult]:
        return self.prepare_preview(), self.render()

    def cleanup(self):
        shutil.rmtree(self.job_dir, ignore_errors=True)

    # ------------------------------------------------------------------ steps
    def _init(self):
        s = self.spec
        args = ["--template", s.template, "--lang", s.lang or "en", "--size", s.size, "--platform", s.platform, "--fps", s.fps,
                "--duration-limit", s.duration_limit_s]
        if s.input_path:
            args += ["--input", Path(s.input_path).resolve()]
        if s.captions:
            args += ["--captions", s.captions]
        if s.brand:
            if s.brand.palette:
                args += ["--palette", json.dumps(s.brand.palette)]
            if s.brand.fonts:
                args += ["--fonts", json.dumps(s.brand.fonts)]
        self.engine.run("init", *args, timeout=60, step="init")
        if s.lang is None:
            self._patch_job(lang_autodetect=True)

    def _tts(self):
        s = self.spec
        script = self.job_dir / "script.txt"
        script.write_text(s.script or "", encoding="utf-8")
        args = ["--text-file", script]
        if s.tts_provider:
            args += ["--provider", s.tts_provider]
        self.engine.run("tts", *args, timeout=self.spec.timeouts.transcribe, step="tts")

    def _transcribe(self):
        s = self.spec
        args = ["--model", s.whisper_model]
        if s.lang:
            args += ["--lang", s.lang]
        self.engine.run("transcribe", *args, timeout=s.timeouts.transcribe, step="transcribe")
        if s.lang is None:
            detected = self._detected_lang()
            if detected:
                self._patch_job(lang=detected)

    def _detected_lang(self) -> str | None:
        t = self.job_dir / "transcript.txt"
        if not t.exists():
            return None
        m = re.match(r"#\s*language:\s*(\S+)", t.read_text(encoding="utf-8"))
        lang = m.group(1) if m else None
        return None if not lang or lang in ("None", "?") else lang

    def _edit(self):
        s = self.spec
        self.engine.run("analyze", timeout=s.timeouts.edit, step="edit")
        self.engine.run("edit", "--pace", s.pace, timeout=s.timeouts.edit, step="edit")
        jd = self.job_json
        if jd.get("input_kind") == "video" and (self.job_dir / "cam_edit.mp4").exists():
            self.engine.run("media", "--name", "cam", "--video", self.job_dir / "cam_edit.mp4", timeout=s.timeouts.edit, step="edit")

    def _assets(self):
        s = self.spec
        manifest = [a.model_dump(mode="json") for a in s.assets]
        for m in manifest:
            m["path"] = str(Path(m["path"]).resolve())
        mf = self.job_dir / "assets.json"
        mf.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        self.engine.run("assets", "--manifest", mf, timeout=s.timeouts.assets, step="assets")
        bad = [r for r in self._read_json("media/index.json", []) if r.get("error")]
        for r in bad:
            self.warnings.append(f"asset {r.get('name')} skipped: {r['error']}")

    def _plan_context(self) -> PlanContext:
        jd = self.job_json
        words = self._read_json("words_edit.json") or self._read_json("words.json") or []
        te = self.job_dir / "transcript_edit.txt"
        return PlanContext(template=self.spec.template, lang=jd.get("lang") or self.spec.lang or "en", words=words,
                           transcript_edit=te.read_text(encoding="utf-8") if te.exists() else "", brief=self.spec.brief or {},
                           media=jd.get("media", {}), asset_index=self._read_json("media/index.json", []), template_dir=self.template_dir,
                           size=self._size(), platform=self.spec.platform, brand=jd.get("brand", {}), duration_hint=jd.get("duration_hint"))

    def _plan(self):
        ctx = self._plan_context()
        plan = self.planner.plan(ctx)
        if not isinstance(plan, dict) or not plan.get("scenes"):
            raise PipelineError("plan_failed", "planner returned no scenes", step="plan", transient=False)
        plan.setdefault("lang", ctx.lang)
        (self.job_dir / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
        self._patch_job(planner=getattr(self.planner, "name", type(self.planner).__name__))

    def _stills(self):
        try:
            self.engine.run("stills", "--auto", timeout=self.spec.timeouts.stills, offline=self.offline_render, step="stills")
        except PipelineError as e:
            if e.code in ("engine_error", "step_failed"):
                raise PipelineError("plan_invalid", e.message, step="stills", transient=False, detail=e.detail) from e
            raise

    def _render(self):
        r = self.spec.render
        args: list[object] = []
        if r.draft:
            args.append("--draft")
        if r.workers:
            args += ["--workers", r.workers]
        self.engine.run("render", *args, timeout=self.spec.timeouts.render, offline=self.offline_render, step="render")

    def _finalize(self):
        r, t = self.spec.render, self.spec.timeouts.finalize
        self.engine.run("sfx", timeout=t, step="finalize")
        self.engine.run("music", *(["--none"] if r.no_music else []), timeout=t, step="finalize")
        self.engine.run("mix", timeout=t, step="finalize")
        mux: list[object] = []
        if r.watermark:
            mux += ["--watermark", Path(r.watermark).resolve(), "--watermark-pos", r.watermark_pos, "--watermark-opacity", r.watermark_opacity]
        if r.max_height:
            mux += ["--max-height", r.max_height]
        self.engine.run("mux", *mux, timeout=t, step="finalize")
        self.engine.run("qa", timeout=t, step="finalize")

    # ------------------------------------------------------------------ results
    def _size(self) -> tuple[int, int]:
        jd = self.job_json
        return int(jd.get("width", 0)), int(jd.get("height", 0))

    def _preview_result(self) -> PreviewResult:
        jd = self.job_json
        te = self.job_dir / "transcript_edit.txt"
        return PreviewResult(plan=self._read_json("plan.json", {}), contact_sheet=self.job_dir / "qa/contact_sheet.jpg",
                             transcript_edit=te.read_text(encoding="utf-8") if te.exists() else "", words=self._read_json("words_edit.json", []),
                             detected_lang=jd.get("lang"), duration_s=float(jd.get("duration") or jd.get("duration_hint") or 0),
                             planner=jd.get("planner", ""), warnings=list(dict.fromkeys(self.warnings)), asset_index=self._read_json("media/index.json", []))
