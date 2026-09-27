"""Shared fixtures. Everything is generated offline (espeak-ng, ffmpeg lavfi, Pillow)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from vs_worker import fixtures as fx
from vs_worker.engine import VT

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "small")


def _have(*bins):
    return all(shutil.which(b) for b in bins)


needs_tools = pytest.mark.skipif(not _have("ffmpeg", "ffprobe", "espeak-ng"), reason="ffmpeg/espeak-ng missing (run inside the worker image)")


@pytest.fixture(scope="session")
def fixtures_dir(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("fixtures")


@pytest.fixture(scope="session")
def voice_wav(fixtures_dir) -> Path:
    return fx.espeak_voice(fixtures_dir / "voice.wav")


@pytest.fixture(scope="session")
def talking_head_mp4(fixtures_dir, voice_wav) -> Path:
    return fx.test_pattern_video(fixtures_dir / "talking_head.mp4", audio=voice_wav)


@pytest.fixture(scope="session")
def screen_mp4(fixtures_dir) -> Path:
    return fx.test_pattern_video(fixtures_dir / "screen.mp4", seconds=8)


@pytest.fixture(scope="session")
def long_clip(fixtures_dir) -> Path:
    return fx.long_clip(fixtures_dir / "clip90.mp4", seconds=90)


@pytest.fixture(scope="session")
def heic_photo(fixtures_dir) -> Path:
    return fx.heic_photo(fixtures_dir / "photo.heic")


@pytest.fixture(scope="session")
def transparent_png(fixtures_dir) -> Path:
    return fx.transparent_png(fixtures_dir / "cutout.png")


@pytest.fixture(scope="session")
def watermark_png() -> Path:
    p = Path(__file__).resolve().parents[3] / "packages/shared/assets/watermark.png"
    assert p.exists(), p
    return p


def vt(*args, env=None, check=True, timeout=600):
    """Run the engine CLI directly (text logs) and return CompletedProcess."""
    e = {**os.environ, **(env or {})}
    e.pop("VT_JSON", None)
    r = subprocess.run([sys.executable, str(VT), *[str(a) for a in args]], capture_output=True, text=True, env=e, timeout=timeout)
    if check and r.returncode:
        raise AssertionError(f"vt.py {args[0]} failed ({r.returncode}):\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    return r


@pytest.fixture
def job_dir(tmp_path) -> Path:
    return tmp_path / "job"


def make_job(job_dir: Path, template="steps", lang="en", size="9:16", input_path: Path | None = None, extra=()):
    args = ["init", job_dir, "--template", template, "--lang", lang, "--size", size, "--platform", "tiktok", *extra]
    if input_path:
        args += ["--input", input_path]
    return vt(*args)
