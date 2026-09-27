"""Offline test fixtures: synthetic speech (espeak-ng), synthetic footage (ffmpeg testsrc2), HEIC / transparent PNG images.

Used by the worker tests and by CI; nothing here needs the network.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

EN_SENTENCES = ("Here are three tips for better sleep. Keep a fixed bedtime every single night. "
                "Put your phone away one hour before bed. Keep the room cool and dark. Sleep well.")


def _run(cmd: list[object]):
    subprocess.run([str(c) for c in cmd], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def espeak_voice(out: Path, text: str = EN_SENTENCES, voice: str = "en-us", wpm: int = 150) -> Path:
    if not shutil.which("espeak-ng"):
        raise RuntimeError("espeak-ng not installed")
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    _run(["espeak-ng", "-v", voice, "-s", str(wpm), "-w", str(out), text])
    return out


def test_pattern_video(out: Path, seconds: float = 8, size: str = "640x360", fps: int = 30, audio: Path | None = None) -> Path:
    """Synthetic screen recording (testsrc2). With `audio`, the voice track is muxed in (talking-head stand-in)."""
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    cmd: list[object] = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=size={size}:rate={fps}"]
    if audio:
        cmd += ["-i", audio, "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
    else:
        cmd += ["-t", str(seconds)]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", out]
    _run(cmd)
    return out


def long_clip(out: Path, seconds: float = 90, size: str = "320x240", fps: int = 15, with_audio: bool = True) -> Path:
    """A 90 s clip (with a tone track) to test trimming and audio dropping."""
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    cmd: list[object] = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=size={size}:rate={fps}"]
    if with_audio:
        cmd += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000", "-map", "0:v", "-map", "1:a", "-c:a", "aac"]
    cmd += ["-t", str(seconds), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p", out]
    _run(cmd)
    return out


def transparent_png(out: Path, size=(600, 800), color=(255, 64, 64, 255)) -> Path:
    """Product cut-out: a coloured rounded shape on a fully transparent canvas."""
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([size[0] * 0.2, size[1] * 0.1, size[0] * 0.8, size[1] * 0.9], radius=60, fill=color)
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "PNG")
    return out


def heic_photo(out: Path, size=(1600, 1200), rotate_exif: bool = True) -> Path:
    """A HEIC photo with an EXIF orientation tag (6 = rotate 90° CW) so conversion must transpose and strip it."""
    import pillow_heif
    from PIL import Image, ImageDraw
    pillow_heif.register_heif_opener()
    im = Image.new("RGB", size, (30, 120, 200))
    d = ImageDraw.Draw(im)
    d.rectangle([40, 40, size[0] // 2, size[1] // 2], fill=(250, 200, 40))   # asymmetric marker to detect rotation
    exif = Image.Exif()
    if rotate_exif:
        exif[0x0112] = 6
    exif[0x010F] = "FixtureCam"  # Make, must be gone after conversion
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, format="HEIF", quality=80, exif=exif.tobytes())
    return out


def jpeg_photo(out: Path, size=(1200, 900), color=(20, 160, 90)) -> Path:
    from PIL import Image
    Image.new("RGB", size, color).save(out, "JPEG", quality=85)
    return Path(out)


def numbered_images(dirpath: Path, n: int = 5, size=(900, 900)) -> list[Path]:
    """Five distinct solid-colour images with a big number, for top-five placement tests."""
    from PIL import Image, ImageDraw, ImageFont
    dirpath = Path(dirpath); dirpath.mkdir(parents=True, exist_ok=True)
    cols = [(230, 60, 60), (60, 160, 230), (60, 200, 120), (240, 180, 40), (170, 80, 220)]
    out = []
    for i in range(n):
        im = Image.new("RGB", size, cols[i % len(cols)])
        d = ImageDraw.Draw(im)
        f: ImageFont.FreeTypeFont | ImageFont.ImageFont
        try:
            f = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf", 400)
        except OSError:
            f = ImageFont.load_default()
        d.text((size[0] * 0.3, size[1] * 0.15), str(i + 1), fill=(255, 255, 255), font=f)
        p = dirpath / f"img{i + 1}.jpg"; im.save(p, "JPEG", quality=90); out.append(p)
    return out
