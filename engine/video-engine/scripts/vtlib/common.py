"""Shared helpers: paths, job files, presets, subprocess wrappers."""
from __future__ import annotations

import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[2]          # .../skills/video-engine
SKILLS_DIR = ENGINE_DIR.parent                              # .../skills
RUNTIME_DIR = ENGINE_DIR / "runtime"
CACHE_DIR = Path(os.environ.get("VT_CACHE", Path.home() / ".cache" / "video-studio"))
# VT_OFFLINE=1: every network call fails fast instead of hanging (render must work with no network).
OFFLINE = os.environ.get("VT_OFFLINE", "") not in ("", "0", "false", "no")
# VT_JSON=1 (or `vt.py --json`): one JSON object per log line for machine consumers.
JSON_LOGS = os.environ.get("VT_JSON", "") not in ("", "0", "false", "no")

SIZE_PRESETS = {
    "9:16": (1080, 1920), "vertical": (1080, 1920), "portrait": (1080, 1920), "tiktok": (1080, 1920),
    "reels": (1080, 1920), "shorts": (1080, 1920), "story": (1080, 1920),
    "4:5": (1080, 1350), "feed": (1080, 1350),
    "1:1": (1080, 1080), "square": (1080, 1080),
    "16:9": (1920, 1080), "landscape": (1920, 1080), "youtube": (1920, 1080), "horizontal": (1920, 1080),
    "4k-9:16": (2160, 3840), "4k-16:9": (3840, 2160), "720p-9:16": (720, 1280), "720p-16:9": (1280, 720),
    "2:3": (1080, 1620), "3:4": (1080, 1440), "21:9": (2520, 1080),
}
PLATFORMS = ["tiktok", "reels", "shorts", "youtube", "linkedin", "x", "none"]


def set_json_logs(on: bool = True):
    global JSON_LOGS
    JSON_LOGS = bool(on)


def _emit(level: str, msg: str, stream, **fields):
    if JSON_LOGS:
        rec = {"ts": round(time.time(), 3), "level": level, "msg": msg}
        rec.update({k: v for k, v in fields.items() if v is not None})
        stream.write(json.dumps(rec, ensure_ascii=False) + "\n")
    else:
        prefix = "[vt] ERROR: " if level == "error" else "[vt] "
        extra = "  " + " ".join(f"{k}={v}" for k, v in fields.items() if v is not None) if fields else ""
        stream.write(prefix + msg + extra + "\n")
    stream.flush()


def log(*a, **fields):
    """Human log line, or one JSON object per line when JSON logs are on.

    Keyword fields (e.g. step="render", progress=0.4) become JSON keys; in text mode they are appended.
    """
    _emit("info", " ".join(str(x) for x in a), sys.stdout, **fields)


def warn(*a, **fields):
    _emit("warning", " ".join(str(x) for x in a), sys.stdout, **fields)


def progress(step: str, frac: float, msg: str = "", **fields):
    """Structured progress event (0..1) for the worker; a plain line in text mode."""
    _emit("progress", msg or step, sys.stdout, step=step, progress=round(max(0.0, min(1.0, frac)), 3), **fields)


def die(msg: str, code: int = 2, error_code: str | None = None):
    _emit("error", msg, sys.stderr, error_code=error_code)
    sys.exit(code)


# Child processes started through run(); terminated on SIGTERM so the CLI stops cleanly.
CHILDREN: set = set()


def run(cmd, check=True, capture=False, quiet=True, timeout=None):
    """Run a command list. Raises with stderr tail on failure."""
    if isinstance(cmd, str):
        cmd = cmd.split()
    cmd = [str(c) for c in cmd]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE if capture or quiet else None,
                         stderr=subprocess.PIPE if capture or quiet else None, text=True)
    CHILDREN.add(p)
    try:
        out, err = p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill(); p.communicate()
        raise RuntimeError(f"Command timed out after {timeout}s: {' '.join(cmd)[:300]}")
    finally:
        CHILDREN.discard(p)
    p.stdout, p.stderr = out, err  # keep the CompletedProcess-like shape callers expect
    if check and p.returncode != 0:
        tail = (err or "")[-1500:]
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(cmd)[:300]}\n{tail}")
    return p


def _terminate_children():
    for p in list(CHILDREN):
        try:
            p.terminate()
        except Exception:
            pass
    deadline = time.time() + 3
    for p in list(CHILDREN):
        try:
            p.wait(timeout=max(0.05, deadline - time.time()))
        except Exception:
            try:
                p.kill()
            except Exception:
                pass


def install_signal_handlers():
    """SIGTERM/SIGINT: stop child processes (ffmpeg, Chromium) and exit 143/130 without half-written files lying around
    unnoticed. The worker enforces timeouts; this makes the CLI a good citizen when it is killed."""
    def handler(signum, frame):
        _emit("error", f"received signal {signum}, stopping", sys.stderr, error_code="interrupted")
        _terminate_children()
        raise SystemExit(128 + signum)
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            signal.signal(sig, handler)
        except (ValueError, OSError):
            pass  # not in the main thread


class OfflineError(OSError):
    pass


def _is_local(address) -> bool:
    if not isinstance(address, tuple) or not address:
        return True  # AF_UNIX paths and abstract sockets
    host = str(address[0])
    return host in ("localhost", "127.0.0.1", "::1", "0.0.0.0", "::", "") or host.startswith("127.")


def install_offline_guard():
    """Make any non-loopback socket connection fail immediately (VT_OFFLINE=1).

    Local connections stay allowed because Playwright talks to Chromium over loopback/pipes.
    HF_HUB_OFFLINE keeps faster-whisper from checking the Hub for the baked-in model.
    """
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    if getattr(socket.socket, "_vt_guarded", False):
        return
    orig_connect, orig_connect_ex = socket.socket.connect, socket.socket.connect_ex

    def connect(self, address):
        if not _is_local(address):
            raise OfflineError(f"network disabled by VT_OFFLINE=1 (tried to reach {address[0]})")
        return orig_connect(self, address)

    def connect_ex(self, address):
        if not _is_local(address):
            raise OfflineError(f"network disabled by VT_OFFLINE=1 (tried to reach {address[0]})")
        return orig_connect_ex(self, address)

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.socket._vt_guarded = True


if OFFLINE:
    install_offline_guard()


def parse_size(s: str | None):
    """'9:16' / '1080x1920' / 'vertical' -> (w, h). Dimensions are forced even for H.264."""
    if not s:
        return None
    s = str(s).strip().lower().replace(" ", "")
    if s in SIZE_PRESETS:
        return SIZE_PRESETS[s]
    m = re.match(r"^(\d+)[x×*](\d+)$", s)
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        return w - w % 2, h - h % 2
    m = re.match(r"^(\d+(?:\.\d+)?):(\d+(?:\.\d+)?)$", s)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        if a <= b:
            w = 1080; h = round(1080 * b / a)
        else:
            h = 1080; w = round(1080 * a / b)
        return w - w % 2, h - h % 2
    raise ValueError(f"Unrecognized size '{s}'. Use a preset ({', '.join(sorted(SIZE_PRESETS))}), W x H like 1080x1920, or a ratio like 9:16.")


def load_json(p, default=None):
    p = Path(p)
    if not p.exists():
        return default
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(p, data):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class Job:
    """A job folder holds every artifact of one video."""

    def __init__(self, path):
        self.dir = Path(path).resolve()
        self.file = self.dir / "job.json"
        self.data = load_json(self.file, {}) or {}

    def save(self):
        save_json(self.file, self.data)

    def p(self, name) -> Path:
        return self.dir / name

    @property
    def size(self):
        return self.data["width"], self.data["height"]

    def template_dir(self) -> Path:
        name = self.data.get("template")
        if not name:
            die("job.json has no template. Run: vt.py init <job> --template <name> ...")
        d = SKILLS_DIR / name
        if not (d / "template.js").exists():
            avail = sorted(x.name for x in SKILLS_DIR.iterdir() if (x / "template.js").exists())
            die(f"Template '{name}' not found next to video-engine. Installed templates: {', '.join(avail)}")
        return d

    def voice(self) -> Path | None:
        for n in ("voice_edit.wav", "voice_clean.wav"):
            if self.p(n).exists():
                return self.p(n)
        return None

    def words(self):
        w = load_json(self.p("words_edit.json")) or load_json(self.p("words.json")) or []
        return w


def ffprobe_duration(path) -> float:
    p = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], capture=True)
    try:
        return float(p.stdout.strip())
    except ValueError:
        return 0.0


def has_video_stream(path) -> bool:
    p = run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)], capture=True, check=False)
    return "video" in (p.stdout or "")


def has_audio_stream(path) -> bool:
    p = run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=codec_type", "-of", "csv=p=0", str(path)], capture=True, check=False)
    return "audio" in (p.stdout or "")


def which(x):
    return shutil.which(x)
