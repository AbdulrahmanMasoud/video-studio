"""Plan validation, editable fields, asset slots, edits by path, media insertion."""
from __future__ import annotations

import json

import pytest

from vs_worker.engine import ENGINE_DIR
from vs_worker.planner.assets import CURATED_MEDIA_FIELDS, media_fields
from vs_worker.planner.schema import (
    apply_asset_changes,
    apply_text_edits,
    asset_slots,
    editable_fields,
    get_path,
    set_path,
    template_scene_types,
    validate_plan,
)

from .test_fallback_planner import SCRIPT, synth_words


def example(template):
    p = json.loads((ENGINE_DIR / template / "examples/plan.example.json").read_text())
    n = len(p.pop("demoScript").split()); p.pop("demoMedia", None)
    return p, n


def test_media_fields_parsed_from_skill_tables():
    for t, expected in CURATED_MEDIA_FIELDS.items():
        got = media_fields(t)
        assert set(expected) <= set(got), (t, got)
        assert got[-1] == "media.media"
    assert media_fields("steps") == ["media.media"]


def test_template_scene_types_include_common():
    assert set(template_scene_types("steps")) == {"hook", "count", "step", "outro", "text", "media"}


def test_validate_example_plans_all_templates():
    for d in sorted(ENGINE_DIR.iterdir()):
        f = d / "examples/plan.example.json"
        if not f.exists():
            continue
        plan, n = example(d.name)
        errs = validate_plan(plan, d.name, n, known_media=None)
        assert errs == [], (d.name, errs)


def test_validate_rejects_bad_anchor_scene_type_and_asset():
    plan, n = example("top-five")
    bad = json.loads(json.dumps(plan)); bad["scenes"][1]["start"] = f"w:{n + 50}"
    errs = validate_plan(bad, "top-five", n)
    assert errs and "missing word index" in errs[0]
    bad = json.loads(json.dumps(plan)); bad["scenes"][1]["type"] = "ranking"
    errs = validate_plan(bad, "top-five", n)
    assert errs and 'type "ranking" is not defined' in errs[0]
    bad = json.loads(json.dumps(plan)); bad["scenes"][1]["media"] = "asset_99"
    errs = validate_plan(bad, "top-five", n, known_media={"asset_1"})
    assert errs and 'unknown asset "asset_99"' in errs[0]
    assert validate_plan({"scenes": []}, "top-five", n)  # schema: min 1 scene
    assert validate_plan("nope", "top-five", n) == ["plan must be a JSON object"]
    ok = json.loads(json.dumps(plan)); ok["scenes"][1]["media"] = "asset_1"
    assert validate_plan(ok, "top-five", n, known_media={"asset_1"}) == []


def test_editable_fields_cover_texts_not_times():
    plan, _ = example("steps")
    fields = editable_fields(plan)
    paths = {f["path"] for f in fields}
    assert "scenes[0].title" in paths and "scenes[2].card.bad.text" in paths and "scenes[2].card.highlights[0].text" in paths
    assert not any(p.endswith(".start") or p.endswith(".at") or p.endswith(".type") or ".icon" in p for p in paths)
    f0 = next(f for f in fields if f["path"] == "scenes[0].title")
    assert f0["value"] == "How to write a great prompt" and f0["maxLen"] == 60 and f0["label"].startswith("hook")
    quiz, _ = example("quiz")
    qf = {f["path"]: f for f in editable_fields(quiz)}
    assert "scenes[0].options[0].text" in qf
    quiz_ar = json.loads((ENGINE_DIR / "quiz/examples/plan.ar.json").read_text())
    assert "labels.question" in {f["path"] for f in editable_fields(quiz_ar)}


def test_apply_text_edits_roundtrip_and_rejects_non_editable():
    plan, _ = example("steps")
    out = apply_text_edits(plan, [{"path": "scenes[0].title", "value": "  New title  "}, {"path": "scenes[2].card.bad.text", "value": "x" * 500}])
    assert out["scenes"][0]["title"] == "New title" and len(out["scenes"][2]["card"]["bad"]["text"]) == 120
    assert plan["scenes"][0]["title"] == "How to write a great prompt"  # original untouched
    with pytest.raises(ValueError):
        apply_text_edits(plan, [{"path": "scenes[0].start", "value": "0"}])
    with pytest.raises(ValueError):
        apply_text_edits(plan, [{"path": "scenes[0].title", "value": 5}])


def test_asset_slots_and_swap_remove_insert():
    plan, n = example("top-five")
    words = synth_words(SCRIPT)
    slots = asset_slots(plan, "top-five")
    assert [p for p, _ in slots] == [f"scenes[{i}].media" for i in range(1, 6)] and all(a is None for _, a in slots)
    changes = [{"path": "scenes[1].media", "asset": "asset_1"}, {"path": "scenes[2].media", "asset": "asset_2"}]
    out = apply_asset_changes(plan, "top-five", words, changes=changes, known_assets={"asset_1", "asset_2"})
    assert dict(asset_slots(out, "top-five", include_empty=False)) == {"scenes[1].media": "asset_1", "scenes[2].media": "asset_2"}
    out2 = apply_asset_changes(out, "top-five", words, changes=[{"path": "scenes[1].media", "asset": None}], known_assets={"asset_1", "asset_2"})
    assert "media" not in out2["scenes"][1]
    with pytest.raises(ValueError):
        apply_asset_changes(out, "top-five", words, changes=[{"path": "scenes[0].title", "asset": "asset_1"}], known_assets={"asset_1"})
    with pytest.raises(ValueError):
        apply_asset_changes(out, "top-five", words, changes=[{"path": "scenes[1].media", "asset": "asset_9"}], known_assets={"asset_1"})
    # insert a full-frame media scene mid-way: the interrupted scene resumes after it
    plan_s, n_s = example("steps")
    words = synth_words(" ".join(["word"] * n_s))  # a transcript as long as the example's demo script
    ins = apply_asset_changes(plan_s, "steps", words, inserts=[{"asset": "asset_2", "at_word": 9, "dur": 2.0}], known_assets={"asset_2"})
    types = [s["type"] for s in ins["scenes"]]
    i = types.index("media")
    assert ins["scenes"][i]["media"] == "asset_2" and ins["scenes"][i]["start"] == "w:9-0.1" and ins["scenes"][i]["end"] == "w:9+1.9"
    assert types.count("media") == 1 and len(ins["scenes"]) >= len(plan_s["scenes"]) + 1
    assert validate_plan(ins, "steps", n_s, known_media={"asset_2"}) == []
    with pytest.raises(ValueError):
        apply_asset_changes(plan_s, "steps", words, inserts=[{"asset": "asset_2", "at_word": 999, "dur": 2}], known_assets={"asset_2"})


def test_path_helpers():
    d = {"a": [{"b": 1}]}
    assert get_path(d, "a[0].b") == 1 and get_path(d, "a[3].b", "x") == "x"
    set_path(d, "a[0].c.d", 5); assert d["a"][0]["c"]["d"] == 5
    set_path(d, "a[0].b", None, delete_if_none=True); assert "b" not in d["a"][0]
