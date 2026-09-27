"""Turn user footage and images into things the browser runtime can show frame-accurately.

Images: any Pillow-readable format plus HEIC/HEIF (pillow-heif) and WebP. EXIF rotation is applied and all metadata
is stripped. Alpha is kept (PNG) so product cut-outs work with `--fit contain`. A 40 MP pixel guard rejects bombs.
Clips: extracted to a JPG frame sequence (optionally trimmed with --start/--duration). Their audio is dropped unless
`keep_audio` is set, in which case it is saved next to the frames and mixed in at the scene time by `vt.py mix`.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np

from .common import ffprobe_duration, has_audio_stream, has_video_stream, load_json, log, run, save_json, warn

MAX_PIXELS = 40_000_000           # decompression-bomb guard
MAX_SIDE = 4096                   # downscale huge photos; Chromium does not need more
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".gif", ".bmp", ".tif", ".tiff", ".avif"}
CLIP_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}


def _open_image(src: Path):
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    if src.suffix.lower() in (".heic", ".heif", ".avif"):
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
            if src.suffix.lower() == ".avif":
                pillow_heif.register_avif_opener()
        except ImportError:
            raise RuntimeError("HEIC/HEIF/AVIF needs the pillow-heif package (pip install pillow-heif)")
    im = Image.open(src)
    im.load()  # raises DecompressionBombError above MAX_PIXELS*2, we also check explicitly
    if im.width * im.height > MAX_PIXELS:
        raise ValueError(f"image too large: {im.width}x{im.height} ({im.width * im.height / 1e6:.0f} MP > {MAX_PIXELS / 1e6:.0f} MP)")
    im = ImageOps.exif_transpose(im)  # apply rotation, then drop EXIF by re-saving without info
    return im


def convert_image(src, dst_base: Path):
    """Normalise any supported image to PNG (alpha) or JPEG (opaque) at <= MAX_SIDE px. Returns (path, w, h, has_alpha)."""
    im = _open_image(Path(src))
    has_alpha = im.mode in ("RGBA", "LA", "PA") or (im.mode == "P" and "transparency" in im.info)
    im = im.convert("RGBA" if has_alpha else "RGB")
    if has_alpha:
        a = np.asarray(im.getchannel("A"))
        has_alpha = bool((a < 250).any())
        if not has_alpha:
            im = im.convert("RGB")
    if max(im.size) > MAX_SIDE:
        k = MAX_SIDE / max(im.size)
        im = im.resize((max(1, int(im.width * k)), max(1, int(im.height * k))))
    dst = Path(dst_base).with_suffix(".png" if has_alpha else ".jpg")
    if has_alpha:
        im.save(dst, "PNG", optimize=True)
    else:
        im.save(dst, "JPEG", quality=92)  # no exif= argument: metadata is stripped
    return dst, im.width, im.height, has_alpha


def add_video(job, name, src, fit="cover", box=None, fps=None, start=0.0, duration=None, keep_audio=False, max_duration=None):
    """Extract a JPG frame sequence scaled to cover the output frame (or a box 'WxH')."""
    W, H = job.size
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(f"clip not found: {src}")
    if not has_video_stream(src):
        raise ValueError(f"not a video file (no video stream): {src.name}")
    if box:
        bw, bh = [int(x) for x in box.lower().split("x")]
    else:
        bw, bh = W, H
    fps = fps or job.data.get("fps", 30)
    total = ffprobe_duration(src)
    start = max(0.0, float(start or 0))
    avail = max(0.0, total - start) if total else None
    if duration is None and max_duration and avail and avail > max_duration:
        duration = max_duration
    if duration is not None and avail is not None:
        duration = min(float(duration), avail)
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
    cmd += ["-an", "-vf", f"fps={fps},{vf}", "-q:v", "3", str(d / "%06d.jpg")]
    run(cmd)
    count = len(list(d.glob("*.jpg")))
    entry = {"type": "video", "dir": d.resolve().as_uri(), "fps": fps, "count": count, "ext": "jpg", "offset": 0, "fit": fit,
             "duration": round(count / fps, 3), "source_start": start, "width": bw, "height": bh}
    if keep_audio and has_audio_stream(src):
        wav = job.p(f"media/{name}.wav")
        acmd = ["ffmpeg", "-y", "-v", "error"]
        if start:
            acmd += ["-ss", str(start)]
        acmd += ["-i", str(src)]
        if duration:
            acmd += ["-t", str(duration)]
        acmd += ["-vn", "-ac", "2", "-ar", "48000", str(wav)]
        run(acmd)
        entry["audio"] = str(wav)
    media = job.data.setdefault("media", {})
    media[name] = entry
    job.save()
    log(f"media '{name}': {count} frames at {bw}x{bh}@{fps}" + (f" (from {start}s)" if start else "") + (" +audio" if entry.get("audio") else ""))
    return entry


def add_image(job, name, src, fit="cover"):
    d = job.p("media"); d.mkdir(exist_ok=True)
    dst, w, h, alpha = convert_image(src, d / name)
    for other in d.glob(name + ".*"):  # remove a stale copy with the other extension
        if other != dst and other.suffix in (".png", ".jpg"):
            other.unlink()
    entry = {"type": "image", "src": dst.resolve().as_uri(), "fit": fit, "width": w, "height": h, "alpha": alpha}
    job.data.setdefault("media", {})[name] = entry
    job.save()
    log(f"media '{name}': image {Path(src).name} -> {dst.name} {w}x{h}" + (" (alpha)" if alpha else ""))
    return entry


def kind_of(path) -> str:
    ext = Path(path).suffix.lower()
    if ext in IMAGE_EXT:
        return "image"
    if ext in CLIP_EXT:
        return "clip"
    return "clip" if has_video_stream(path) else "image"


def register_assets(job, manifest, max_clip_seconds=60.0):
    """Register many assets in one call from a manifest list and write media/index.json.

    Manifest items: {"name": "asset_1", "path": "/abs/file.heic", "kind": "image|clip" (optional), "description": "...",
                     "fit": "cover|contain", "start": 0, "duration": 5, "keep_audio": false}
    Returns the index list. Failing items are reported in the index with "error" and do not stop the others.
    """
    if isinstance(manifest, (str, Path)):
        manifest = load_json(manifest, [])
    if isinstance(manifest, dict):
        manifest = manifest.get("assets", [])
    index = []
    for item in manifest:
        name, path = item.get("name"), item.get("path")
        if not name or not path:
            index.append({"name": name, "error": "manifest item needs name and path"}); continue
        src = Path(path)
        rec = {"name": name, "original": src.name, "description": item.get("description") or ""}
        try:
            if not src.exists():
                raise FileNotFoundError(f"asset not found: {src}")
            kind = item.get("kind") or kind_of(src)
            rec["kind"] = kind
            rec["bytes"] = src.stat().st_size
            if kind == "image":
                fit = item.get("fit") or "cover"
                e = add_image(job, name, src, fit)
                rec.update({"width": e["width"], "height": e["height"], "alpha": e["alpha"], "fit": fit})
                if e["alpha"] and fit == "cover":
                    rec["fit"] = "contain"; job.data["media"][name]["fit"] = "contain"; job.save()  # cut-outs must not be cropped
            else:
                e = add_video(job, name, src, item.get("fit") or "cover", None, None, float(item.get("start") or 0), item.get("duration"),
                              bool(item.get("keep_audio")), max_duration=max_clip_seconds)
                rec.update({"width": e["width"], "height": e["height"], "duration": e["duration"], "alpha": False, "fit": e["fit"],
                            "has_audio": bool(e.get("audio"))})
        except Exception as ex:  # keep going; the caller decides
            rec["error"] = str(ex)[:300]
            warn(f"asset '{name}' skipped: {rec['error']}", asset=name)
        index.append(rec)
    save_json(job.p("media/index.json"), index)
    ok = [r for r in index if not r.get("error")]
    log(f"assets: {len(ok)}/{len(index)} registered -> media/index.json")
    return index


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
