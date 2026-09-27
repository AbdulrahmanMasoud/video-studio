"""Run the engine CLI (vt.py) as a subprocess with JSON logs, a timeout and progress callbacks.

The CLI contract (see engine/video-engine/SKILL.md) is the only interface to the engine. Every call gets
`--json`, so stdout is one JSON object per line: {"level": "info|warning|progress|error", "msg": ..., ...}.
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .errors import PipelineError

ROOT = Path(os.environ.get("VS_REPO_ROOT", Path(__file__).resolve().parents[3]))
ENGINE_DIR = Path(os.environ.get("VS_ENGINE_DIR", ROOT / "engine"))
VT = ENGINE_DIR / "video-engine" / "scripts" / "vt.py"


@dataclass
class EngineEvent:
    level: str
    msg: str
    fields: dict = field(default_factory=dict)

    @property
    def progress(self) -> float | None:
        v = self.fields.get("progress")
        return float(v) if v is not None else None


@dataclass
class EngineResult:
    returncode: int
    events: list[EngineEvent]
    stdout_tail: str
    stderr_tail: str
    seconds: float

    @property
    def warnings(self) -> list[str]:
        return [e.msg for e in self.events if e.level == "warning"]

    @property
    def error(self) -> EngineEvent | None:
        errs = [e for e in self.events if e.level == "error"]
        return errs[-1] if errs else None


class EngineRunner:
    """Executes `vt.py --json <cmd> JOB ...` and turns log lines into events."""

    def __init__(self, job_dir: Path, *, python: str | None = None, env: dict | None = None, on_event: Callable[[EngineEvent], None] | None = None,
                 vt_path: Path | None = None):
        self.job_dir = Path(job_dir)
        self.python = python or sys.executable
        self.env = env or {}
        self.on_event = on_event
        self.vt = Path(vt_path or VT)
        if not self.vt.exists():
            raise PipelineError("engine_missing", f"engine CLI not found at {self.vt}", transient=False)

    def run(self, cmd: str, *args, timeout: float | None = None, offline: bool = False, step: str | None = None, check: bool = True) -> EngineResult:
        argv = [self.python, str(self.vt), "--json", cmd, str(self.job_dir), *[str(a) for a in args]]
        if cmd in ("doctor", "templates", "fonts"):
            argv = [self.python, str(self.vt), "--json", cmd, *[str(a) for a in args]]
        env = {**os.environ, **self.env, "VT_JSON": "1", "PYTHONUNBUFFERED": "1"}
        if offline:
            env["VT_OFFLINE"] = "1"
        events: list[EngineEvent] = []
        out_lines: list[str] = []
        err_lines: list[str] = []
        t0 = time.time()
        p = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, start_new_session=True)

        def pump(stream, sink, parse):
            for line in stream:
                sink.append(line.rstrip("\n"))
                if len(sink) > 400:
                    del sink[:100]
                if parse:
                    ev = _parse(line)
                    if ev:
                        events.append(ev)
                        if self.on_event:
                            try:
                                self.on_event(ev)
                            except Exception:
                                pass

        t_out = threading.Thread(target=pump, args=(p.stdout, out_lines, True), daemon=True)
        t_err = threading.Thread(target=pump, args=(p.stderr, err_lines, True), daemon=True)
        t_out.start(); t_err.start()
        timed_out = False
        try:
            p.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            _kill_group(p)
        t_out.join(timeout=5); t_err.join(timeout=5)
        res = EngineResult(p.returncode if not timed_out else -9, events, "\n".join(out_lines[-30:]), "\n".join(err_lines[-30:]), time.time() - t0)
        if timed_out:
            raise PipelineError("timeout", f"vt.py {cmd} exceeded {timeout:.0f}s", step=step or cmd, transient=True)
        if check and res.returncode != 0:
            err = res.error
            code = (err.fields.get("error_code") if err else None) or "engine_error"
            msg = err.msg if err else (res.stderr_tail.strip().splitlines() or ["engine failed"])[-1]
            raise PipelineError(code, msg, step=step or cmd, detail={"returncode": res.returncode, "stderr": res.stderr_tail[-1500:]})
        return res


def _parse(line: str) -> EngineEvent | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith("{"):
        try:
            d = json.loads(line)
            lvl = str(d.pop("level", "info")); msg = str(d.pop("msg", "")); d.pop("ts", None)
            return EngineEvent(lvl, msg, d)
        except json.JSONDecodeError:
            pass
    if line.startswith("[vt] ERROR:"):
        return EngineEvent("error", line[len("[vt] ERROR:"):].strip())
    if line.startswith("[vt]"):
        return EngineEvent("info", line[4:].strip())
    return EngineEvent("stderr", line)


def _kill_group(p: subprocess.Popen):
    try:
        os.killpg(p.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        p.wait(timeout=5)
