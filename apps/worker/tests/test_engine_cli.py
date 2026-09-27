"""Engine CLI contract additions from Phase 1: JSON logs, error codes, duration limit, offline guard, fonts cache."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from vs_worker.engine import VT, EngineRunner
from vs_worker.errors import PipelineError

from .conftest import make_job, needs_tools, vt

pytestmark = needs_tools


def test_json_logs_one_object_per_line(job_dir, voice_wav):
    r = vt("--json", "init", job_dir, "--template", "steps", "--lang", "en", "--size", "9:16", "--input", voice_wav)
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    assert lines, r.stdout
    for l in lines:
        d = json.loads(l)
        assert {"ts", "level", "msg"} <= set(d)
    assert any("job ready" in json.loads(l)["msg"] for l in lines)


def test_init_refuses_without_lang_and_size_with_error_code(job_dir):
    r = vt("--json", "init", job_dir, "--template", "steps", check=False)
    assert r.returncode == 2
    err = json.loads(r.stderr.strip().splitlines()[-1])
    assert err["level"] == "error" and err["error_code"] == "intake_missing"


def test_init_duration_limit(job_dir, voice_wav):
    r = vt("--json", "init", job_dir, "--template", "steps", "--lang", "en", "--size", "9:16", "--input", voice_wav, "--duration-limit", "3", check=False)
    assert r.returncode == 2
    err = json.loads(r.stderr.strip().splitlines()[-1])
    assert err["error_code"] == "input_too_long"
    # generous limit passes and records the input duration
    vt("init", job_dir, "--template", "steps", "--lang", "en", "--size", "9:16", "--input", voice_wav, "--duration-limit", "600")
    jd = json.loads((job_dir / "job.json").read_text())
    assert 5 < jd["input_duration"] < 60


def test_init_rejects_non_media_file(job_dir, tmp_path):
    bad = tmp_path / "notes.txt"; bad.write_text("hello")
    r = vt("--json", "init", job_dir, "--template", "steps", "--lang", "en", "--size", "9:16", "--input", bad, check=False)
    assert r.returncode == 2
    assert json.loads(r.stderr.strip().splitlines()[-1])["error_code"] == "input_invalid"


def test_offline_guard_fails_fast(tmp_path):
    """With VT_OFFLINE=1 a fresh cache dir cannot fetch fonts; the call must fail immediately, not hang."""
    code = ("import sys; sys.path.insert(0, %r); from vtlib import fonts, common\n"
            "assert common.OFFLINE\n"
            "try:\n    fonts._fetch('https://fonts.googleapis.com/css2?family=Inter')\nexcept common.OfflineError as e:\n    print('blocked', e)\n"
            "else:\n    raise SystemExit('not blocked')\n"
            "import socket\n"
            "try:\n    socket.create_connection(('1.1.1.1', 80), timeout=5)\nexcept common.OfflineError as e:\n    print('socket blocked')\n"
            "else:\n    raise SystemExit('socket not blocked')\n").replace("%r", repr(str(VT.parent)))
    env = {**os.environ, "VT_OFFLINE": "1", "VT_CACHE": str(tmp_path / "emptycache")}
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=30)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "blocked" in r.stdout and "socket blocked" in r.stdout


def test_offline_font_resolution_uses_cache_or_fallback(tmp_path):
    """Offline + empty cache: resolve_fonts returns quickly with system fallbacks and a warning (no exception)."""
    code = ("import sys, time; sys.path.insert(0, %r); from vtlib import fonts\n"
            "t=time.time(); css, stacks = fonts.resolve_fonts('ar', ['display','body']); "
            "print(round(time.time()-t,2), stacks['display'])").replace("%r", repr(str(VT.parent)))
    env = {**os.environ, "VT_OFFLINE": "1", "VT_CACHE": str(tmp_path / "emptycache")}
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, timeout=30)
    assert r.returncode == 0, r.stderr
    last = r.stdout.strip().splitlines()[-1]          # warnings about uncached fonts precede the result line
    secs = float(last.split()[0])
    assert secs < 2.0
    assert "system-ui" in last and "not in the cache" in r.stdout


@pytest.mark.skipif(not Path(os.environ.get("VT_CACHE", "/nonexistent")).joinpath("fonts").exists(), reason="no pre-cached font dir (VT_CACHE)")
def test_precached_fonts_cover_latin_and_arabic_display_roles():
    cache = Path(os.environ["VT_CACHE"]) / "fonts"
    for fam in ("archivo", "inter", "alexandria", "ibm-plex-sans-arabic"):
        assert (cache / fam / "font.css").exists(), f"missing cached family {fam}"


def test_engine_runner_maps_errors_and_events(job_dir, voice_wav):
    events = []
    er = EngineRunner(job_dir, on_event=events.append)
    with pytest.raises(PipelineError) as ei:
        er.run("init", "--template", "steps", "--lang", "en", "--size", "9:16", "--input", voice_wav, "--duration-limit", "1", step="init")
    assert ei.value.code == "input_too_long" and ei.value.user_error and not ei.value.transient
    res = er.run("init", "--template", "steps", "--lang", "en", "--size", "9:16", "--input", voice_wav)
    assert res.returncode == 0 and any("job ready" in e.msg for e in res.events)


def test_engine_runner_timeout_kills_process(job_dir, voice_wav):
    make_job(job_dir, input_path=voice_wav)
    er = EngineRunner(job_dir)
    with pytest.raises(PipelineError) as ei:
        er.run("transcribe", "--model", "small", timeout=0.5, step="transcribe")
    assert ei.value.code == "timeout" and ei.value.transient


def test_sigterm_stops_cli_cleanly(job_dir, voice_wav):
    """vt.py must exit on SIGTERM (143) and leave no child ffmpeg/chromium behind."""
    import signal
    import time
    make_job(job_dir, input_path=voice_wav)
    cmd = [sys.executable, str(VT), "--json", "transcribe", str(job_dir), "--model", "small"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(1.5)
    p.send_signal(signal.SIGTERM)
    out, err = p.communicate(timeout=20)
    assert p.returncode in (143, -15), (p.returncode, err[-500:])
    assert "interrupted" in err or "signal" in err
