"""Engine-backed planner tests (Phase 2 DoD): mock planner through the real validator, a top-five job with 5 fixture images placed
in their ranks (contact sheet shows them), and the edit / swap / insert round-trips."""
from __future__ import annotations

import json
import os

import numpy as np
import pytest
from PIL import Image

from vs_worker import fixtures as fx
from vs_worker.errors import PipelineError
from vs_worker.llm.mock import MockLLM
from vs_worker.llm.settings import LLMSettings
from vs_worker.pipeline import Pipeline
from vs_worker.planner.llm_planner import LLMPlanner
from vs_worker.spec import AssetSpec, JobSpec

from .conftest import needs_tools

pytestmark = [needs_tools, pytest.mark.slow]
MODEL = os.environ.get("WHISPER_MODEL", "small")
COLOURS = [(230, 60, 60), (60, 160, 230), (60, 200, 120), (240, 180, 40), (170, 80, 220)]


def settings(**kw):
    base = dict(planner_model="mock/planner", fast_model="mock/fast", vision_model="mock/vision", free_tier_model="mock/fast", paid_tier_model="mock/planner")
    base.update(kw)
    return LLMSettings(**base)


def colour_fraction(img_path, rgb, tol=48):  # assets are re-encoded as JPEG (chroma subsampling shifts saturated greens by ~40)
    a = np.asarray(Image.open(img_path).convert("RGB")).astype(int)
    m = (np.abs(a - np.array(rgb)).max(axis=2) <= tol)
    return float(m.mean())


@pytest.fixture(scope="module")
def five_images(tmp_path_factory):
    return fx.numbered_images(tmp_path_factory.mktemp("imgs"), 5)


def test_top_five_places_each_image_in_its_rank(tmp_path, voice_wav, five_images):
    spec = JobSpec(job_id="t5", template="top-five", size="9:16", lang="en", input_path=voice_wav, whisper_model=MODEL,
                   assets=[AssetSpec(name=f"asset_{i + 1}", path=p, description="" if i % 2 else f"item {i + 1}") for i, p in enumerate(five_images)])
    mock = MockLLM()
    pipe = Pipeline(spec, tmp_path, planner=LLMPlanner(mock, settings()))
    preview = pipe.prepare_preview()
    assert preview.planner == "llm"
    ranks = [s for s in preview.plan["scenes"] if s["type"] == "rank"]
    assert [r["media"] for r in ranks] == ["asset_1", "asset_2", "asset_3", "asset_4", "asset_5"]
    assert {s["asset"] for s in preview.asset_slots} == {f"asset_{i}" for i in range(1, 6)} and preview.unused_assets == []
    # assets without a user description were described by the (mock) vision model
    by = {a["name"]: a for a in preview.asset_index}
    assert by["asset_1"]["description"] == "item 1" and by["asset_1"].get("description_source") == "user"
    assert by["asset_2"]["description"] and by["asset_2"]["description_source"] == "ai"
    assert preview.llm["calls"] >= 2 and {u for u in preview.llm["by_task"]} >= {"plan", "describe_assets"}
    # every rank still shows its image (non-placeholder pixels in the media area): each fixture is a distinct solid colour
    stills = sorted((pipe.job_dir / "qa").glob("still_*.png"))
    scenes = json.loads((pipe.job_dir / "render/scenes.json").read_text())
    assert len(stills) == len(scenes)
    rank_stills = [st for st, sc in zip(stills, scenes, strict=True) if sc["type"] == "rank"]
    assert len(rank_stills) == 5
    for k, st in enumerate(rank_stills):
        frac = colour_fraction(st, COLOURS[k])
        assert frac > 0.02, f"rank {k + 1}: only {frac:.3%} of pixels match asset colour {COLOURS[k]}"
    # the engine also drew the contact sheet
    assert preview.contact_sheet.exists()
    # -------- round trips: edit a text, swap an asset, remove one, insert an unused asset as a full-frame shot
    p2 = pipe.apply_texts([{"path": "scenes[1].title", "value": "Edited rank title"}])
    assert p2.plan["scenes"][1]["title"] == "Edited rank title"
    with pytest.raises(PipelineError) as ei:
        pipe.apply_texts([{"path": "scenes[1].start", "value": "0"}])
    assert ei.value.code == "plan_invalid"
    p3 = pipe.apply_assets(changes=[{"path": "scenes[1].media", "asset": "asset_5"}, {"path": "scenes[5].media", "asset": None}])
    assert dict((s["path"], s["asset"]) for s in p3.asset_slots)["scenes[1].media"] == "asset_5" and "asset_5" not in p3.unused_assets
    assert p3.plan["scenes"][5].get("media") is None
    p4 = pipe.apply_assets(inserts=[{"asset": "asset_3", "at_word": 5, "dur": 2.0}])
    media_scenes = [s for s in p4.plan["scenes"] if s["type"] == "media"]
    assert media_scenes and media_scenes[0]["media"] == "asset_3" and p4.contact_sheet.exists()
    with pytest.raises(PipelineError):
        pipe.apply_assets(changes=[{"path": "scenes[1].media", "asset": "asset_404"}])


def test_mock_planner_full_pipeline_with_llm_edit_decision(tmp_path, voice_wav):
    """A scripted edit decision drops two words; the plan is re-anchored to the shorter edited transcript and renders."""
    mock = MockLLM(script=[{"drop": [{"from": 1, "to": 2, "reason": "test"}]}])
    spec = JobSpec(job_id="ed", template="steps", size="1:1", lang="en", input_path=voice_wav, whisper_model=MODEL)
    pipe = Pipeline(spec, tmp_path, planner=LLMPlanner(mock, settings()))
    preview = pipe.prepare_preview()
    assert pipe.job_json["edit_drops"] == "w:1-w:2"
    n_raw = len(pipe._read_json("words.json"))
    assert len(preview.words) == n_raw - 2
    assert mock.requests[0]["task"] == "edit_decision" and mock.requests[1]["task"] == "plan"
    assert preview.editable_fields and preview.llm["by_task"]["edit_decision"]["calls"] == 1


def test_arabic_example_plan_is_used_for_arabic(tmp_path, voice_wav):
    """Language forced to Arabic (the fixture voice is English): the mock returns the Arabic example and the RTL plan validates in the engine."""
    spec = JobSpec(job_id="ar", template="quiz", size="9:16", lang="ar", input_path=voice_wav, whisper_model=MODEL, llm_edit_decisions=False)
    mock = MockLLM()
    pipe = Pipeline(spec, tmp_path, planner=LLMPlanner(mock, settings()))
    preview = pipe.prepare_preview()
    assert preview.plan["lang"] == "ar" and preview.plan["labels"]["question"] == "سؤال" and preview.contact_sheet.exists()
