"""Asset ingestion: HEIC conversion (rotation applied, EXIF stripped), alpha kept, clip trimming, audio dropping, manifest index."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image

from .conftest import make_job, needs_tools, vt

pytestmark = needs_tools


def _probe(path, *entries):
    cmd = ["ffprobe", "-v", "error", "-show_entries", ",".join(entries), "-of", "json", str(path)]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def test_heic_is_converted_rotated_and_stripped(job_dir, heic_photo, voice_wav):
    make_job(job_dir, input_path=voice_wav)
    vt("media", job_dir, "--name", "photo", "--image", heic_photo)
    jd = json.loads((job_dir / "job.json").read_text())
    m = jd["media"]["photo"]
    out = Path(m["src"].replace("file://", ""))
    assert out.suffix == ".jpg" and out.exists()
    im = Image.open(out)
    # source was 1600x1200 with EXIF orientation 6 → rotated to portrait 1200x1600
    assert (im.width, im.height) == (1200, 1600) == (m["width"], m["height"])
    assert not im.getexif(), "EXIF must be stripped"
    assert m["alpha"] is False


def test_transparent_png_keeps_alpha_and_contain_fit(job_dir, transparent_png, voice_wav):
    make_job(job_dir, input_path=voice_wav)
    vt("media", job_dir, "--name", "cutout", "--image", transparent_png, "--fit", "contain")
    m = json.loads((job_dir / "job.json").read_text())["media"]["cutout"]
    out = Path(m["src"].replace("file://", ""))
    assert out.suffix == ".png" and m["alpha"] is True and m["fit"] == "contain"
    im = Image.open(out)
    assert im.mode == "RGBA" and im.getpixel((5, 5))[3] == 0  # corner stays transparent


def test_webp_supported(job_dir, tmp_path, voice_wav):
    make_job(job_dir, input_path=voice_wav)
    src = tmp_path / "pic.webp"
    Image.new("RGB", (640, 480), (200, 30, 90)).save(src, "WEBP")
    vt("media", job_dir, "--name", "pic", "--image", src)
    m = json.loads((job_dir / "job.json").read_text())["media"]["pic"]
    assert (m["width"], m["height"]) == (640, 480)


def test_decompression_bomb_rejected(job_dir, tmp_path, voice_wav):
    make_job(job_dir, input_path=voice_wav)
    src = tmp_path / "huge.png"
    # 9000x5000 = 45 MP > 40 MP guard; solid colour PNG compresses to a few KB
    Image.new("1", (9000, 5000), 1).save(src, "PNG")
    r = vt("--json", "media", job_dir, "--name", "huge", "--image", src, check=False)
    assert r.returncode == 2
    assert json.loads(r.stderr.strip().splitlines()[-1])["error_code"] == "asset_invalid"


def test_clip_trimmed_and_audio_dropped(job_dir, long_clip, voice_wav):
    make_job(job_dir, input_path=voice_wav)
    vt("media", job_dir, "--name", "broll", "--video", long_clip, "--start", "10", "--duration", "5")
    m = json.loads((job_dir / "job.json").read_text())["media"]["broll"]
    assert m["type"] == "video" and abs(m["duration"] - 5.0) < 0.2 and m["source_start"] == 10.0
    frames = list((job_dir / "media/broll").glob("*.jpg"))
    assert 145 <= len(frames) <= 152  # 5 s @ 30 fps
    assert "audio" not in m and not (job_dir / "media/broll.wav").exists()


def test_clip_keep_audio(job_dir, long_clip, voice_wav):
    make_job(job_dir, input_path=voice_wav)
    vt("media", job_dir, "--name", "broll", "--video", long_clip, "--duration", "3", "--keep-audio")
    m = json.loads((job_dir / "job.json").read_text())["media"]["broll"]
    wav = Path(m["audio"])
    assert wav.exists()
    d = float(_probe(wav, "format=duration")["format"]["duration"])
    assert abs(d - 3.0) < 0.2


def test_assets_manifest_writes_index(job_dir, heic_photo, transparent_png, long_clip, tmp_path, voice_wav):
    make_job(job_dir, input_path=voice_wav)
    manifest = [
        {"name": "asset_1", "path": str(heic_photo), "description": "product photo"},
        {"name": "asset_2", "path": str(transparent_png)},                       # alpha → fit forced to contain
        {"name": "asset_3", "path": str(long_clip), "start": 2, "duration": 5},   # 90 s clip trimmed to 5 s
        {"name": "asset_4", "path": str(long_clip)},                              # no duration → capped at --max-clip-seconds
        {"name": "asset_5", "path": str(tmp_path / "missing.jpg")},               # error, must not stop the others
    ]
    mf = tmp_path / "assets.json"; mf.write_text(json.dumps(manifest))
    vt("assets", job_dir, "--manifest", mf, "--max-clip-seconds", "4")
    index = json.loads((job_dir / "media/index.json").read_text())
    by = {r["name"]: r for r in index}
    assert by["asset_1"]["kind"] == "image" and by["asset_1"]["description"] == "product photo" and not by["asset_1"]["alpha"]
    assert by["asset_2"]["alpha"] is True and by["asset_2"]["fit"] == "contain"
    assert by["asset_3"]["kind"] == "clip" and abs(by["asset_3"]["duration"] - 5) < 0.2 and by["asset_3"]["has_audio"] is False
    assert abs(by["asset_4"]["duration"] - 4) < 0.2
    assert "error" in by["asset_5"] and "not found" in by["asset_5"]["error"]
    assert set(json.loads((job_dir / "job.json").read_text())["media"]) == {"asset_1", "asset_2", "asset_3", "asset_4"}
    # --strict turns the failure into exit 2
    r = vt("--json", "assets", job_dir, "--manifest", mf, "--strict", check=False)
    assert r.returncode == 2 and json.loads(r.stderr.strip().splitlines()[-1])["error_code"] == "asset_invalid"
