"""LLMPlanner: storyboard with a provider-agnostic LLM, validated by Pydantic + the engine (stills), with repair attempts,
optional vision review, editable fields, asset slots and cost accounting. Falls back to the deterministic planner when the LLM is out.
"""
from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path

from ..errors import PipelineError
from ..llm.client import LLMError
from ..llm.settings import LLMSettings
from . import fallback
from .assets import AssetDescriber, media_fields
from .edit_decision import decide_drops
from .prompts import build_system_prompt, build_user_message, repair_message
from .schema import asset_slots, editable_fields, template_scene_types, validate_plan

log = logging.getLogger("vs_worker.planner")

VISION_CHECKLIST = ("Review this contact sheet (one frame per scene) of a short video storyboard. Check: text overflowing or cut off, text hidden "
                    "behind captions/UI, wrong language or writing direction, empty or placeholder-looking frames, unreadable tiny text. "
                    'Return {"fixes": [{"path": "<editable field path>", "value": "<shorter/corrected text>"}]} using ONLY the paths listed, '
                    'or {"fixes": []} when everything is fine. Fix at most 6 fields.')


class LLMPlanner:
    """Implements the Planner protocol used by Pipeline plus decide_edits() and describe_assets()."""
    name = "llm"

    def __init__(self, llm, settings: LLMSettings | None = None, *, tier: str = "paid", fallback_on_failure: bool = True, engine_dir: Path | None = None):
        self.llm = llm
        self.settings = settings or LLMSettings.from_env()
        self.tier = tier
        self.fallback_on_failure = fallback_on_failure
        self.engine_dir = engine_dir
        self.usage: list[dict] = []
        self.last: dict = {}

    # ------------------------------------------------------------------ Planner protocol
    def plan(self, ctx) -> dict:
        """ctx: PlanContext (pipeline.py). Needs ctx.validate(plan) -> list[str] (writes plan.json + runs stills) when available."""
        model = self.settings.planner_for_tier(self.tier)
        n = len(ctx.words)
        assets = [a for a in ctx.asset_index if not a.get("error")]
        known = set(ctx.media.keys())
        scene_types = template_scene_types(ctx.template, self.engine_dir)
        system = build_system_prompt(ctx.template, ctx.lang, n, scene_types, assets, self.engine_dir)
        user = build_user_message(transcript_edit=ctx.transcript_edit, brief=ctx.brief, lang=ctx.lang, size=ctx.size, platform=ctx.platform,
                                  template=ctx.template, assets=assets, brand=ctx.brand, engine_dir=self.engine_dir)
        messages = [{"role": "user", "content": user}]
        mock_ctx = {"template": ctx.template, "lang": ctx.lang, "n_words": n, "assets": assets, "media_paths": media_fields(ctx.template, self.engine_dir)}
        attempts: list[dict] = []
        plan: dict | None = None
        llm_error: LLMError | None = None
        try:
            for attempt in range(1, self.settings.max_attempts + 1):
                resp = self._call(system, messages, model, "plan" if attempt == 1 else "repair", mock_ctx)
                candidate = resp.data
                errors = validate_plan(candidate, ctx.template, n, known, self.engine_dir)
                if not errors and getattr(ctx, "validate", None):
                    errors = ctx.validate(candidate)
                attempts.append({"attempt": attempt, "model": resp.model, "errors": errors[:8]})
                if not errors:
                    plan = candidate
                    break
                log.info("plan attempt %d rejected: %s", attempt, errors[:3])
                messages = messages + [{"role": "assistant", "content": json.dumps(candidate, ensure_ascii=False)[:20000]},
                                       {"role": "user", "content": repair_message(errors)}]
        except LLMError as e:
            llm_error = e
            attempts.append({"attempt": len(attempts) + 1, "error": str(e)[:300]})
            log.warning("LLM unavailable: %s", e)
        if plan is None and llm_error is not None and self.fallback_on_failure:
            plan = fallback.plan(ctx.template, ctx.words, ctx.lang, brief=ctx.brief, media=ctx.media, duration=ctx.duration_hint)
            self.name = "fallback"
            errs = ctx.validate(plan) if getattr(ctx, "validate", None) else []
            if errs:
                raise PipelineError("plan_failed", "fallback plan rejected: " + "; ".join(errs[:3]), step="plan", transient=False)
        elif plan is None and llm_error is not None:
            self.last = {"planner": "llm", "attempts": attempts, "usage": list(self.usage)}
            raise PipelineError("llm_unavailable", str(llm_error), step="plan", transient=True) from llm_error
        elif plan is None:
            self.last = {"planner": "llm", "attempts": attempts, "usage": list(self.usage)}
            last_errors = (attempts[-1].get("errors") or ["?"])[:3]
            raise PipelineError("plan_failed", f"no valid plan after {len(attempts)} attempts: " + "; ".join(last_errors), step="plan", transient=False,
                                detail={"attempts": attempts})
        else:
            self.name = "llm"
        if plan is not None and self.name == "llm" and self.settings.vision_review and getattr(ctx, "contact_sheet", None):
            plan = self._vision_review(plan, ctx, model)
        slots = [{"path": p, "asset": a} for p, a in asset_slots(plan, ctx.template, self.engine_dir)]
        self.last = {"planner": self.name, "model": model, "attempts": attempts, "usage": list(self.usage),
                     "editable_fields": editable_fields(plan), "asset_slots": slots}
        return plan

    # ------------------------------------------------------------------ extra services
    def decide_edits(self, analysis: str, transcript: str, n_words: int, lang: str) -> str | None:
        try:
            spec, usage = decide_drops(self.llm, self.settings.fast_model, analysis, transcript, n_words, lang)
        except LLMError as e:
            log.warning("edit decision skipped (LLM): %s", e)
            return None
        self.usage += usage
        return spec

    def describe_assets(self, index: list[dict], media: dict, job_dir: Path, lang: str) -> list[dict]:
        try:
            index, usage = AssetDescriber(self.llm, self.settings.fast_model).describe(index, media, job_dir, lang)
        except LLMError as e:
            log.warning("asset description skipped (LLM): %s", e)
            return index
        self.usage += usage
        return index

    # ------------------------------------------------------------------ internals
    def _call(self, system, messages, model, task, mock_ctx):
        kw = {"model": model, "task": task}
        if getattr(self.llm, "name", "") == "mock":
            kw["context"] = mock_ctx
        resp = self.llm.complete_json(system, messages, **kw)
        self.usage.append(resp.usage())
        return resp

    def _vision_review(self, plan: dict, ctx, model: str) -> dict:
        sheet = Path(ctx.contact_sheet)
        if not sheet.exists():
            return plan
        fields = editable_fields(plan)
        user = "Editable fields (path → current value):\n" + "\n".join(f"{f['path']} → {f['value']}" for f in fields[:80]) + "\n\n" + VISION_CHECKLIST
        extra: dict = {"context": {}} if getattr(self.llm, "name", "") == "mock" else {}
        try:
            resp = self.llm.complete_json("You are a meticulous video QA reviewer.", [{"role": "user", "content": user}],
                                          model=self.settings.vision_model or model, task="vision_review", images=[sheet], **extra)
        except LLMError as e:
            log.warning("vision review skipped: %s", e)
            return plan
        self.usage.append(resp.usage())
        fixes = (resp.data or {}).get("fixes") or []
        if not fixes:
            return plan
        from .schema import apply_text_edits
        try:
            fixed = apply_text_edits(plan, [{"path": f.get("path"), "value": f.get("value")} for f in fixes[:6]])
        except ValueError as e:
            log.info("vision fixes ignored: %s", e)
            return plan
        if getattr(ctx, "validate", None) and ctx.validate(fixed):
            return plan  # keep the validated original if the fixes broke something
        return fixed


def make_planner(mode: str | None = None, *, tier: str = "paid", settings: LLMSettings | None = None, engine_dir: Path | None = None,
                 overrides: dict | None = None, mock_script: list | None = None) -> Callable | object:
    """Factory: mode 'llm' (LiteLLM), 'mock' (MockLLM), 'fallback' (deterministic). Default from env PLANNER_MODE, else 'llm'."""
    import os

    from ..llm.client import LLMClient
    from ..llm.mock import MockLLM
    from ..pipeline import FallbackPlanner

    mode = (mode or os.environ.get("PLANNER_MODE") or "llm").lower()
    settings = settings or LLMSettings.from_env(overrides=overrides)
    if mode == "fallback":
        return FallbackPlanner()
    if mode == "mock":
        return LLMPlanner(MockLLM(engine_dir, script=mock_script), settings, tier=tier, engine_dir=engine_dir)
    return LLMPlanner(LLMClient(settings), settings, tier=tier, engine_dir=engine_dir)
