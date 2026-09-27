"""Phase 1 Definition of done: the pipeline runs the espeak fixture with `small` whisper through
transcribe → edit → deterministic fallback plan → stills → render (--draft) → mux with watermark, and the
MP4 exists, has audio, and QA loudness is within ±2 LU of the target."""
from __future__ import annotations

import json
import os
import subprocess

import pytest

from vs_worker.errors import PipelineError
from vs_worker.pipeline import Pipeline
from vs_worker.spec import AssetSpec, JobSpec, RenderOptions

from .conftest import needs_tools

pytestmark = [needs_tools, pytest.mark.slow]
MODEL = os.environ.get("WHISPER_MODEL", "small")


def _has_audio(mp4):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True).stdout
    return "audio" in o


def test_full_pipeline_steps_draft_watermark(tmp_path, voice_wav, watermark_png, transparent_png, heic_photo):
    events = []
    spec = JobSpec(job_id="job1", template="steps", size="9:16", lang=None, platform="tiktok", input_path=voice_wav, whisper_model=MODEL,
                   assets=[AssetSpec(name="asset_a", path=transparent_png), AssetSpec(name="asset_b", path=heic_photo, description="a photo")],
                   render=RenderOptions(draft=True, watermark=watermark_png, max_height=720, workers=2))
    pipe = Pipeline(spec, tmp_path, on_event=events.append)
    preview = pipe.prepare_preview()
    # transcription + edit
    assert preview.detected_lang == "en"
    assert len(preview.words) >= 20 and preview.transcript_edit.startswith("# language")
    assert preview.planner == "fallback"
    assert preview.plan["scenes"][0]["type"] == "hook" and preview.contact_sheet.exists()
    assert {a["name"] for a in preview.asset_index} == {"asset_a", "asset_b"}
    steps = [e.step for e in events if e.status == "done"]
    assert steps == ["init", "transcribe", "edit", "assets", "plan", "stills"]

    result = pipe.render()
    assert result.final_mp4.exists() and result.final_mp4.stat().st_size > 50_000
    assert _has_audio(result.final_mp4)
    rep = result.qa_report
    assert rep["has_audio"] and abs(rep["lufs"] - (-14.0)) <= 2.0, rep
    assert rep["true_peak"] <= -0.5, rep  # engine QA rule; AAC adds ~0.3 dB overshoot after the -1.5 dBTP loudnorm
    assert rep["issues"] == [], rep["issues"]
    # draft (0.5) of 1080x1920 is 540x960; max_height 720 does not upscale, so the delivery is 540x960
    assert result.output_size == (540, 960) and (rep["width"], rep["height"]) == (540, 960)
    assert not any("resolution" in i for i in rep["issues"]), rep["issues"]
    assert result.final_sheet and result.final_sheet.exists()
    assert any(e.step == "render" and e.status == "progress" for e in events), "render progress events expected"
    assert [e.step for e in events if e.status == "done"][-2:] == ["render", "finalize"]
    # idempotency: re-running render on the same folder works and overwrites
    result2 = pipe.render()
    assert result2.final_mp4.exists()
    pipe.cleanup()
    assert not pipe.job_dir.exists()


def test_pipeline_video_input_mirror(tmp_path, talking_head_mp4):
    spec = JobSpec(job_id="job2", template="mirror", size="1:1", lang="en", input_path=talking_head_mp4, whisper_model=MODEL,
                   render=RenderOptions(draft=True, workers=2, no_music=True), brief={"title": "Sleep tips"})
    pipe = Pipeline(spec, tmp_path)
    preview = pipe.prepare_preview()
    jd = pipe.job_json
    assert jd["input_kind"] == "video" and "cam" in jd["media"], "camera footage must be registered after the edit"
    assert preview.plan["scenes"][0] == {"type": "title", "start": 0, "text": "Sleep tips", "at": 0.1, "end": preview.plan["scenes"][0]["end"]}
    result = pipe.render()
    assert result.final_mp4.exists() and _has_audio(result.final_mp4)
    assert result.output_size == (540, 540)


def test_apply_plan_reruns_stills_and_rejects_bad_anchor(tmp_path, voice_wav):
    spec = JobSpec(job_id="job3", template="steps", size="9:16", lang="en", input_path=voice_wav, whisper_model=MODEL)
    pipe = Pipeline(spec, tmp_path)
    preview = pipe.prepare_preview()
    plan = json.loads(json.dumps(preview.plan))
    plan["scenes"][0]["title"] = "Edited title"
    p2 = pipe.apply_plan(plan)
    assert p2.plan["scenes"][0]["title"] == "Edited title" and p2.contact_sheet.exists()
    bad = json.loads(json.dumps(plan)); bad["scenes"][1]["start"] = "w:9999"
    with pytest.raises(PipelineError) as ei:
        pipe.apply_plan(bad)
    assert ei.value.code == "plan_invalid" and "missing word index" in ei.value.message
    unknown = json.loads(json.dumps(plan)); unknown["scenes"][1]["type"] = "nope"
    with pytest.raises(PipelineError) as ei:
        pipe.apply_plan(unknown)
    assert ei.value.code == "plan_invalid" and "not defined by this template" in ei.value.message


def test_user_errors_are_not_transient(tmp_path, voice_wav):
    spec = JobSpec(job_id="job4", template="steps", size="9:16", lang="en", input_path=voice_wav, whisper_model=MODEL, duration_limit_s=2)
    with pytest.raises(PipelineError) as ei:
        Pipeline(spec, tmp_path).prepare_preview()
    assert ei.value.code == "input_too_long" and ei.value.user_error and not ei.value.transient and ei.value.step == "init"


def test_tts_script_job(tmp_path):
    script = "Which planet is the hottest? Mercury, Venus, Mars or Jupiter? The answer is Venus."
    spec = JobSpec(job_id="job5", template="quiz", size="16:9", lang="en", script=script, tts_provider="espeak", whisper_model=MODEL)
    pipe = Pipeline(spec, tmp_path)
    preview = pipe.prepare_preview()
    assert pipe.job_json["tts"]["provider"] == "espeak"
    assert len(preview.words) >= 8 and all(s["type"] == "text" for s in preview.plan["scenes"])
