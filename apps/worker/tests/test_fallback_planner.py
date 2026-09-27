"""Deterministic fallback planner: sections on pauses, valid anchors, steps/mirror/generic storyboards."""
from __future__ import annotations

import json
import re

import pytest

from vs_worker.planner import fallback
from vs_worker.planner.transcript import announced_count, sections, title

from .conftest import make_job, needs_tools, vt


def synth_words(script: str, gap_after_sentence=0.7):
    t, out = 0.3, []
    for tok in script.split():
        out.append({"w": tok, "s": round(t, 3), "e": round(t + 0.25, 3)})
        t += 0.3 + (gap_after_sentence if re.search(r"[.!?؟]$", tok) else 0)
    return out


SCRIPT = ("Here are three tips for better sleep. First, keep a fixed bedtime every night no matter what. "
          "Second, put your phone away one hour before bed. Third, keep the room cool and dark. Sleep well tonight.")


def _check_anchors(plan, n_words):
    for m in re.finditer(r'"we?:(\d+)', json.dumps(plan)):
        assert int(m.group(1)) < n_words, f"anchor out of range: {m.group(0)}"


def test_sections_split_on_pauses_and_merge_short():
    words = synth_words(SCRIPT)
    secs = sections(words)
    assert 3 <= len(secs) <= 6
    assert secs[0][0] == 0 and secs[-1][1] == len(words) - 1
    for (_a, b), (c, _d) in zip(secs, secs[1:], strict=False):
        assert c == b + 1  # contiguous, no gaps
    assert all(words[b]["e"] - words[a]["s"] >= 1.5 for a, b in secs[:-1])


def test_title_uses_four_to_six_words():
    words = synth_words(SCRIPT)
    t = title(words, 0, 6)
    assert 4 <= len(t.split()) <= 6 and not t.endswith(".")
    assert t == "Here are three tips for better"  # max 6 words, "sleep." never reached; no trailing stopword


def test_announced_count_detects_number_words():
    words = synth_words(SCRIPT)
    assert announced_count(words, 0, 6, "en") == (2, 3)
    ar = synth_words("عندي أربع حاجات هتفرق معاك. أولا كون واضح.")
    assert announced_count(ar, 0, 4, "ar") == (1, 4)


def test_steps_plan_shape():
    words = synth_words(SCRIPT)
    plan = fallback.plan("steps", words, "en")
    types = [s["type"] for s in plan["scenes"]]
    assert types[0] == "hook" and types[1] == "count" and types[-1] == "outro"
    assert types.count("step") >= 2
    assert plan["lang"] == "en" and plan["labels"]["prompt"] == "Prompt"
    _check_anchors(plan, len(words))
    assert all(len(s["title"].split()) <= 8 for s in plan["scenes"] if s["type"] == "step")


def test_mirror_plan_shape_without_cam_disables_punch():
    words = synth_words(SCRIPT)
    plan = fallback.plan("mirror", words, "en", media={})
    assert plan["scenes"][0]["type"] == "title"
    assert all(s["type"] == "talk" for s in plan["scenes"][1:])
    assert plan["data"]["punch"] is False
    plan2 = fallback.plan("mirror", words, "en", media={"cam": {"type": "video"}})
    assert "data" not in plan2
    _check_anchors(plan, len(words))


def test_generic_plan_uses_common_text_scene_and_brief_title():
    words = synth_words(SCRIPT)
    plan = fallback.plan("quiz", words, "en", brief={"title": "Sleep better"})
    assert all(s["type"] == "text" for s in plan["scenes"])
    assert plan["scenes"][0]["text"] == "Sleep better" and plan["scenes"][0]["start"] == 0


def test_arabic_labels_and_rtl_plan():
    script = "الذكاء الاصطناعي ذكي جدا، بس مش بيقرا أفكارك. عشان كده عندي أربع حاجات هتفرق معاك. أولا: كون واضح. ثانيا: اديله السياق. الخلاصة: اكتب بوضوح."
    words = synth_words(script)
    plan = fallback.plan("steps", words, "ar")
    assert plan["labels"]["prompt"] == "برومبت" and plan["lang"] == "ar"
    assert plan["scenes"][-1]["label"] == "الخلاصة"


def test_empty_transcript_gives_duration_plan():
    plan = fallback.plan("steps", [], "en", brief={"title": "Hello"}, duration=6)
    assert plan["duration"] == 6 and plan["scenes"][0]["type"] == "text"


@needs_tools
@pytest.mark.parametrize("template", ["steps", "mirror", "quiz", "top-five"])
def test_fallback_plans_validate_in_engine(job_dir, template, voice_wav):
    """The engine (stills --auto) is the ground-truth validator: every fallback plan must render stills without errors."""
    make_job(job_dir, template=template, input_path=voice_wav)
    words = synth_words(SCRIPT)
    (job_dir / "words_edit.json").write_text(json.dumps(words))
    plan = fallback.plan(template, words, "en")
    (job_dir / "plan.json").write_text(json.dumps(plan))
    r = vt("--json", "stills", job_dir, "--auto", "--scale", "0.3", env={"VT_OFFLINE": "1"})
    errs = [l for l in r.stdout.splitlines() if '"level": "error"' in l or "browser" in l.lower()]
    assert not errs, errs
    assert (job_dir / "qa/contact_sheet.jpg").exists()
