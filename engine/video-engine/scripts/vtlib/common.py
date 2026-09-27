"""Shared helpers: paths, job files, presets, subprocess wrappers."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parents[2]          # .../skills/video-engine
SKILLS_DIR = ENGINE_DIR.parent                              # .../skills
RUNTIME_DIR = ENGINE_DIR / "runtime"
CACHE_DIR = Path(os.environ.get("VT_CACHE", Path.home() / ".cache" / "video-studio"))

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


def log(*a):
    print("[vt]", *a, flush=True)


def die(msg: str, code: int = 2):
    print(f"[vt] ERROR: {msg}", file=sys.stderr, flush=True)
    sys.exit(code)


def run(cmd, check=True, capture=False, quiet=True):
    """Run a command list. Raises with stderr tail on failure."""
    if isinstance(cmd, str):
        cmd = cmd.split()
    p = subprocess.run(cmd, stdout=subprocess.PIPE if capture or quiet else None,
                       stderr=subprocess.PIPE if capture or quiet else None, text=True)
    if check and p.returncode != 0:
        tail = (p.stderr or "")[-1500:]
        raise RuntimeError(f"Command failed ({p.returncode}): {' '.join(map(str, cmd))[:300]}\n{tail}")
    return p


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
