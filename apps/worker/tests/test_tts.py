"""TTS provider interface: disabled by default, espeak provider works offline, OpenAI provider needs a key."""
from __future__ import annotations

import json
import os

import pytest

from .conftest import make_job, needs_tools, vt

pytestmark = needs_tools


def test_tts_disabled_by_default(job_dir, tmp_path):
    make_job(job_dir)
    script = tmp_path / "s.txt"; script.write_text("Hello there.")
    env = {k: v for k, v in os.environ.items() if k != "TTS_PROVIDER"}
    env["TTS_PROVIDER"] = "none"
    r = vt("--json", "tts", job_dir, "--text-file", script, env=env, check=False)
    assert r.returncode == 2
    assert json.loads(r.stderr.strip().splitlines()[-1])["error_code"] == "tts_disabled"


def test_espeak_provider_writes_mp3_and_transcribes(job_dir, tmp_path):
    make_job(job_dir)
    script = tmp_path / "s.txt"; script.write_text("Three quick tips for better sleep. Keep a fixed bedtime. Put the phone away.")
    vt("tts", job_dir, "--text-file", script, "--provider", "espeak")
    jd = json.loads((job_dir / "job.json").read_text())
    assert jd["input"].endswith("tts.mp3") and jd["input_kind"] == "audio" and jd["tts"]["provider"] == "espeak"
    assert (job_dir / "tts.mp3").stat().st_size > 5000
    # word timings come from transcription of the generated audio (no provider timings)
    assert not (job_dir / "words.json").exists()
    vt("transcribe", job_dir, "--model", os.environ.get("WHISPER_MODEL", "small"), env={"VT_OFFLINE": "1"})
    words = json.loads((job_dir / "words.json").read_text())
    assert len(words) >= 8


def test_openai_provider_requires_key(job_dir, tmp_path):
    make_job(job_dir)
    script = tmp_path / "s.txt"; script.write_text("Hello.")
    env = {k: v for k, v in os.environ.items() if k != "OPENAI_API_KEY"}
    r = vt("--json", "tts", job_dir, "--text-file", script, "--provider", "openai", env=env, check=False)
    assert r.returncode == 2
    assert json.loads(r.stderr.strip().splitlines()[-1])["error_code"] == "tts_not_configured"


@pytest.mark.network
@pytest.mark.skipif(not os.environ.get("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
def test_openai_provider_real(job_dir, tmp_path):
    make_job(job_dir)
    script = tmp_path / "s.txt"; script.write_text("Hello from the video studio.")
    vt("tts", job_dir, "--text-file", script, "--provider", "openai")
    assert (job_dir / "tts.mp3").stat().st_size > 2000
