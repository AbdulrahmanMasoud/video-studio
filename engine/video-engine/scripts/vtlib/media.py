"""Turn user footage into things the browser runtime can show frame-accurately."""
from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

from .common import ffprobe_duration, has_video_stream, log, run


def add_video(job, name, src, fit="cover", box=None, fps=None, start=0.0, duration=None):
    """Extract a JPG frame sequence scaled to cover the output frame (or a box 'WxH')."""
    W, H = job.size
    if box:
        bw, bh = [int(x) for x in box.lower().split("x")]
    else:
        bw, bh = W, H
    fps = fps or job.data.get("fps", 30)
    d = job.p(f"media/{name}")
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    if fit == "cover":
        vf = f"scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh}"
    else:
        vf = f"scale={bw}:{bh}:force_original_aspect_ratio=decrease,pad={bw}:{bh}:(ow-iw)/2:(oh-ih)/2:color=black"
    cmd = ["ffmpeg", "-y", "-v", "error"]
    if start:
        cmd += ["-ss", str(start)]
    cmd += ["-i", str(src)]
    if duration:
        cmd += ["-t", str(duration)]
    cmd += ["-vf", f"fps={fps},{vf}", "-q:v", "3", str(d / "%06d.jpg")]
    run(cmd)
    count = len(list(d.glob("*.jpg")))
    media = job.data.setdefault("media", {})
    media[name] = {"type": "video", "dir": d.resolve().as_uri(), "fps": fps, "count": count, "ext": "jpg", "offset": 0}
    job.save()
    log(f"media '{name}': {count} frames at {bw}x{bh}@{fps}")


def add_image(job, name, src, fit="cover"):
    d = job.p("media"); d.mkdir(exist_ok=True)
    dst = d / (name + Path(src).suffix.lower())
    shutil.copy(src, dst)
    job.data.setdefault("media", {})[name] = {"type": "image", "src": dst.resolve().as_uri(), "fit": fit}
    job.save()
    log(f"media '{name}': image {Path(src).name}")


def audio_levels(wav, fps=30):
    """Per-frame loudness 0..1 of the voice, for waveforms and audio-reactive motion."""
    try:
        import soundfile as sf
        a, sr = sf.read(str(wav), dtype="float32", always_2d=False)
    except Exception:
        return []
    if a.ndim > 1:
        a = a.mean(axis=1)
    h = int(sr / fps)
    n = len(a) // h
    if n == 0:
        return []
    r = np.sqrt((a[: n * h].reshape(n, h) ** 2).mean(axis=1))
    db = 20 * np.log10(r + 1e-9)
    lv = np.clip((db + 50) / 44, 0, 1)
    sm = np.convolve(lv, np.ones(3) / 3, mode="same")
    return [round(float(x), 3) for x in sm]
