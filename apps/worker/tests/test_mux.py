"""mux: watermark overlay and short-side cap; qa expected-size awareness."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from .conftest import needs_tools, vt

pytestmark = needs_tools


@pytest.fixture(scope="module")
def rendered_job(tmp_path_factory, voice_wav):
    """A tiny job with a solid dark video + the voice, without running Chromium: exercises mux/qa only."""
    job = tmp_path_factory.mktemp("muxjob") / "job"
    vt("init", job, "--template", "steps", "--lang", "en", "--size", "16:9", "--input", voice_wav)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=0x202040:size=1920x1080:rate=30", "-t", "4",
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(job / "video_noaudio.mp4")], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(voice_wav), "-t", "4", "-ar", "48000", "-ac", "2", str(job / "mix.wav")], check=True)
    jd = json.loads((job / "job.json").read_text()); jd["duration"] = 4.0; (job / "job.json").write_text(json.dumps(jd))
    return job


def _frame(mp4, t=2.0):
    out = Path(mp4).with_suffix(".png")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", str(mp4), "-frames:v", "1", str(out)], check=True)
    return np.asarray(Image.open(out).convert("RGB")).astype(int)


def _size(mp4):
    o = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(mp4)],
                       capture_output=True, text=True, check=True).stdout.strip().split(",")
    return int(o[0]), int(o[1])


def test_plain_mux_copies_video(rendered_job):
    vt("mux", rendered_job, "--out", rendered_job / "plain.mp4")
    assert _size(rendered_job / "plain.mp4") == (1920, 1080)
    fr = _frame(rendered_job / "plain.mp4")
    assert fr.mean() < 80  # dark everywhere, no overlay


def test_watermark_bottom_right_is_visible(rendered_job, watermark_png):
    vt("mux", rendered_job, "--out", rendered_job / "wm.mp4", "--watermark", watermark_png, "--watermark-pos", "br", "--watermark-opacity", "0.6")
    fr = _frame(rendered_job / "wm.mp4")
    h, w, _ = fr.shape
    br = fr[int(h * 0.80):int(h * 0.98), int(w * 0.78):int(w * 0.98)]
    tl = fr[:int(h * 0.2), :int(w * 0.2)]
    assert br.max() > 150, "watermark pixels expected in the bottom-right corner"
    assert tl.max() < 90, "top-left must stay untouched"
    # 60 % opacity: bright pixels are lighter than the background but not pure white
    bright = br[br.sum(axis=2) > 300]
    assert len(bright) > 50 and bright.mean() < 250


def test_max_height_caps_short_side_and_qa_accepts(rendered_job):
    vt("mux", rendered_job, "--max-height", "720")
    assert _size(rendered_job / "final.mp4") == (1280, 720)
    jd = json.loads((rendered_job / "job.json").read_text())
    assert jd["output_size"] == [1280, 720]
    vt("qa", rendered_job)
    rep = json.loads((rendered_job / "qa/report.json").read_text())
    assert (rep["width"], rep["height"]) == (1280, 720)
    assert not any("resolution" in i for i in rep["issues"]), rep["issues"]
    assert "delivered at 1280x720" in rep.get("note", "")


def test_watermark_plus_downscale_portrait(tmp_path, voice_wav, watermark_png):
    job = tmp_path / "job"
    vt("init", job, "--template", "steps", "--lang", "en", "--size", "9:16", "--input", voice_wav)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:size=1080x1920:rate=30", "-t", "2",
                    "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(job / "video_noaudio.mp4")], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(voice_wav), "-t", "2", "-ar", "48000", "-ac", "2", str(job / "mix.wav")], check=True)
    vt("mux", job, "--watermark", watermark_png, "--watermark-pos", "tl", "--max-height", "720")
    assert _size(job / "final.mp4") == (720, 1280)
    fr = _frame(job / "final.mp4", 1.0)
    assert fr[:200, :300].max() > 150
