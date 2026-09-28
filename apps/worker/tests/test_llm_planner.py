"""LLMPlanner with the MockLLM: validation loop, repair, rejection, edit decisions, asset description, usage accounting.
These run without the engine (a fake ctx.validate stands in for stills) so they are fast; engine-backed runs are in test_pipeline_llm.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from vs_worker.engine import ENGINE_DIR
from vs_worker.errors import PipelineError
from vs_worker.llm.client import LLMError
from vs_worker.llm.mock import MockLLM, rescale_anchors
from vs_worker.llm.settings import LLMSettings
from vs_worker.pipeline import PlanContext
from vs_worker.planner.edit_decision import validate_drops
from vs_worker.planner.llm_planner import LLMPlanner
from vs_worker.planner.prompts import build_system_prompt, build_user_message, example_plan

from .test_fallback_planner import SCRIPT, synth_words


def settings(**kw):
    base = dict(planner_model="mock/planner", fast_model="mock/fast", vision_model="mock/vision", free_tier_model="mock/fast", paid_tier_model="mock/planner")
    base.update(kw)
    return LLMSettings(**base)


def ctx_for(template="steps", lang="en", assets=(), media=None, tmp_path: Path | None = None):
    words = synth_words(SCRIPT)
    transcript = "\n".join(f"[{i}] {w['w']}@{w['s']:.2f}" for i, w in enumerate(words))
    c = PlanContext(template=template, lang=lang, words=words, transcript_edit=transcript, brief={"title": "Sleep tips"}, media=media or {},
                    asset_index=list(assets), template_dir=ENGINE_DIR / template, size=(1080, 1920), platform="tiktok")
    c.validated: list = []

    def validate(plan):
        c.validated.append(plan)
        return []
    c.validate = validate
    return c


def test_prompt_contains_rules_skill_schema_and_transcript():
    ctx = ctx_for("top-five", assets=[{"name": "asset_1", "kind": "image", "description": "a mug", "has_alpha": True}])
    sys_p = build_system_prompt("top-five", "ar", len(ctx.words), ["intro", "rank", "text", "media"], ctx.asset_index)
    assert "Arabic" in sys_p and "rank.media" in sys_p and "asset_1" in sys_p and "## 4. Scenes" in sys_p and "## Time values" in sys_p
    assert "vt.py" not in sys_p.split("# PLAN SCHEMA")[0].split("## 3.")[0]  # bash 'Produce' section stripped
    user = build_user_message(transcript_edit=ctx.transcript_edit, brief=ctx.brief, lang="ar", size=(1080, 1920), platform="tiktok", template="top-five",
                              assets=ctx.asset_index)
    assert "Sleep tips" in user and '"name": "asset_1"' in user and "[0] Here@" in user and "EXAMPLE" in user
    ex = example_plan("steps", "ar")
    assert ex and ex["plan"]["lang"] == "ar" and len(ex["plan"]["scenes"]) <= 6


def test_mock_plan_accepted_and_usage_recorded():
    ctx = ctx_for("steps")
    planner = LLMPlanner(MockLLM(), settings(), tier="paid")
    plan = planner.plan(ctx)
    assert plan["scenes"][0]["type"] == "hook" and plan["lang"] == "en"
    assert planner.name == "llm" and len(ctx.validated) == 1
    assert planner.last["attempts"] == [{"attempt": 1, "model": "mock/planner", "errors": []}]
    assert planner.last["usage"][0]["task"] == "plan" and planner.last["editable_fields"]
    assert planner.usage[0]["tokens_in"] > 100


def test_free_tier_uses_fast_model():
    ctx = ctx_for("steps")
    mock = MockLLM()
    LLMPlanner(mock, settings(), tier="free").plan(ctx)
    assert mock.requests[0]["model"] == "mock/fast"


def test_bad_anchor_repaired_within_attempts():
    ctx = ctx_for("steps")
    good = MockLLM().example_plan("steps", "en", len(ctx.words), [], [])
    bad = json.loads(json.dumps(good)); bad["scenes"][1]["start"] = "w:9999"
    mock = MockLLM(script=[bad, good])
    planner = LLMPlanner(mock, settings())
    plan = planner.plan(ctx)
    assert plan == good
    att = planner.last["attempts"]
    assert len(att) == 2 and "missing word index" in att[0]["errors"][0] and att[1]["errors"] == []
    assert mock.requests[1]["task"] == "repair" and "rejected the plan" in mock.requests[1]["messages"][-1]["content"]
    assert len(ctx.validated) == 1  # schema errors never reach the engine


def test_engine_errors_feed_the_repair_loop():
    ctx = ctx_for("steps")
    good = MockLLM().example_plan("steps", "en", len(ctx.words), [], [])
    calls = []

    def validate(plan):
        calls.append(plan)
        return ['Scene 2 (step) is only 0.10s long'] if len(calls) == 1 else []
    ctx.validate = validate
    planner = LLMPlanner(MockLLM(script=[good, good]), settings())
    planner.plan(ctx)
    assert len(calls) == 2 and planner.last["attempts"][0]["errors"] == ['Scene 2 (step) is only 0.10s long']


def test_unknown_scene_type_and_asset_rejected_then_plan_failed():
    ctx = ctx_for("top-five", assets=[{"name": "asset_1", "kind": "image"}], media={"asset_1": {"type": "image"}})
    good = MockLLM().example_plan("top-five", "en", len(ctx.words), [], [])
    bad_type = json.loads(json.dumps(good)); bad_type["scenes"][1]["type"] = "ranking"
    bad_asset = json.loads(json.dumps(good)); bad_asset["scenes"][1]["media"] = "asset_7"
    planner = LLMPlanner(MockLLM(script=[bad_type, bad_asset, bad_type]), settings(max_attempts=3))
    with pytest.raises(PipelineError) as ei:
        planner.plan(ctx)
    assert ei.value.code == "plan_failed" and not ei.value.transient
    att = ei.value.detail["attempts"]
    assert 'type "ranking"' in att[0]["errors"][0] and 'unknown asset "asset_7"' in att[1]["errors"][0] and len(att) == 3


def test_llm_down_falls_back_to_deterministic_plan():
    class Down:
        name = "down"
        def complete_json(self, *a, **k):
            raise LLMError("connection refused", transient=True)
    ctx = ctx_for("steps")
    planner = LLMPlanner(Down(), settings())
    plan = planner.plan(ctx)
    assert planner.name == "fallback" and plan["scenes"][0]["type"] == "hook" and ctx.validated
    strict = LLMPlanner(Down(), settings(), fallback_on_failure=False)
    with pytest.raises(PipelineError) as ei:
        strict.plan(ctx_for("steps"))
    assert ei.value.code == "llm_unavailable" and ei.value.transient


def test_mock_fills_media_slots_with_assets():
    assets = [{"name": f"asset_{i}", "kind": "image"} for i in range(1, 6)]
    ctx = ctx_for("top-five", assets=assets, media={f"asset_{i}": {"type": "image"} for i in range(1, 6)})
    plan = LLMPlanner(MockLLM(), settings()).plan(ctx)
    ranks = [s for s in plan["scenes"] if s["type"] == "rank"]
    assert [r["media"] for r in ranks] == ["asset_1", "asset_2", "asset_3", "asset_4", "asset_5"]


def test_vision_review_applies_fixes_once(tmp_path):
    from PIL import Image
    sheet = tmp_path / "contact_sheet.jpg"; Image.new("RGB", (10, 10)).save(sheet)
    ctx = ctx_for("steps"); ctx.contact_sheet = sheet
    good = MockLLM().example_plan("steps", "en", len(ctx.words), [], [])
    mock = MockLLM(script=[good, {"fixes": [{"path": "scenes[0].title", "value": "Shorter title"}, {"path": "scenes[0].start", "value": "9"}]}])
    planner = LLMPlanner(mock, settings(vision_review=True))
    plan = planner.plan(ctx)
    # the bad path makes apply_text_edits fail → whole fix set ignored; test the happy path separately
    assert plan["scenes"][0]["title"] == good["scenes"][0]["title"]
    mock2 = MockLLM(script=[good, {"fixes": [{"path": "scenes[0].title", "value": "Shorter title"}]}])
    ctx2 = ctx_for("steps"); ctx2.contact_sheet = sheet
    plan2 = LLMPlanner(mock2, settings(vision_review=True)).plan(ctx2)
    assert plan2["scenes"][0]["title"] == "Shorter title"
    assert mock2.requests[1]["task"] == "vision_review" and mock2.requests[1]["images"] == [sheet]
    assert len(ctx2.validated) == 2


def test_edit_decision_validation():
    assert validate_drops({"drop": [{"from": 3, "to": 5}, {"from": 10, "to": 10}]}, 40) == "w:3-w:5,w:10-w:10"
    assert validate_drops({"drop": []}, 40) is None
    assert validate_drops({"drop": [{"from": 3, "to": 50}]}, 40) is None            # out of range
    assert validate_drops({"drop": [{"from": 3, "to": 30}]}, 40) is None            # span too long
    assert validate_drops({"drop": [{"from": 1, "to": 5}, {"from": 4, "to": 8}]}, 40) is None   # overlap
    assert validate_drops({"drop": [{"from": 0, "to": 9}, {"from": 20, "to": 29}]}, 40) is None  # > 25 % of words
    assert validate_drops({"drop": "w:1-w:2"}, 40) is None and validate_drops(None, 40) is None
    planner = LLMPlanner(MockLLM(script=[{"drop": [{"from": 2, "to": 3, "reason": "repeat"}]}]), settings())
    assert planner.decide_edits("analysis", "[0] a@0", 40, "en") == "w:2-w:3" and planner.usage[0]["task"] == "edit_decision"


def test_describe_assets_fills_missing_descriptions(tmp_path):
    from PIL import Image
    img = tmp_path / "media" / "asset_1.jpg"; img.parent.mkdir(); Image.new("RGB", (20, 20), (200, 0, 0)).save(img)
    index = [{"name": "asset_1", "kind": "image"}, {"name": "asset_2", "kind": "image", "description": "my desk"}]
    media = {"asset_1": {"type": "image", "src": img.resolve().as_uri()}, "asset_2": {"type": "image", "src": img.resolve().as_uri()}}
    mock = MockLLM(script=[{"descriptions": {"asset_1": "a red square"}}])
    planner = LLMPlanner(mock, settings())
    out = planner.describe_assets(index, media, tmp_path, "en")
    assert out[0]["description"] == "a red square" and out[0]["description_source"] == "ai" and out[1]["description"] == "my desk"
    assert mock.requests[0]["images"] == [img] and mock.requests[0]["model"] == "mock/fast"


def test_rescale_anchors_monotonic():
    plan = {"scenes": [{"start": "w:0"}, {"start": "w:50-0.1", "at": "we:99"}]}
    out = rescale_anchors(plan, 100, 34)
    assert out["scenes"][1]["start"] == "w:17-0.1" and out["scenes"][1]["at"] == "we:33"
