"""Mix voice + music + SFX to platform loudness, mux with picture, and run QA."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .common import ffprobe_duration, has_audio_stream, log, run

TARGETS = {"tiktok": -14, "reels": -14, "shorts": -14, "youtube": -14, "linkedin": -14, "x": -14, "none": -14, "broadcast": -23, "podcast": -16}


def loudness(path):
    p = run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"], capture=True, check=False)
    txt = p.stderr or ""
    tail = txt[txt.rfind("Summary:"):] if "Summary:" in txt else txt
    I = re.search(r"I:\s+(-?[\d.]+) LUFS", tail); TP = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
    return (float(I.group(1)) if I else None, float(TP.group(1)) if TP else None)


def prepare_music_file(src, duration, out):
    """Loop/trim a user-supplied track to the video length with fades."""
    d = ffprobe_duration(src)
    loops = max(0, int(duration // max(d, 0.1)))
    run(["ffmpeg", "-y", "-v", "error", "-stream_loop", str(loops), "-i", str(src), "-t", str(duration),
         "-af", f"afade=t=in:d=0.3,afade=t=out:st={max(0, duration - 1.5)}:d=1.5", "-ar", "48000", "-ac", "2", str(out)])
    return out


def mix(voice, music, sfx, duration, out, lufs=-14.0, music_db=-13.0, sfx_db=2.0, duck=True, clips=None, clip_db=-6.0):
    """clips: [(wav_path, start_seconds, max_seconds)] audio of b-roll clips kept with `media --keep-audio`."""
    inputs, filt, labels = [], [], []
    idx = 0
    if voice:
        inputs += ["-i", str(voice)]
        filt.append(f"[{idx}:a]aformat=channel_layouts=stereo,apad=whole_dur={duration},asplit=2[v][vsc]")
        labels.append("[v]"); vi = idx; idx += 1
    if music:
        inputs += ["-i", str(music)]
        if voice and duck:
            filt.append(f"[{idx}:a]volume={music_db}dB[m0];[m0][vsc]sidechaincompress=threshold=0.02:ratio=5:attack=25:release=400:makeup=1[m]")
        else:
            filt.append(f"[{idx}:a]volume={music_db + (0 if voice else 7)}dB[m]")
            if voice:
                filt.append("[vsc]anullsink")
        labels.append("[m]"); idx += 1
    elif voice:
        filt.append("[vsc]anullsink")
    if sfx:
        inputs += ["-i", str(sfx)]
        filt.append(f"[{idx}:a]volume={sfx_db}dB[s]"); labels.append("[s]"); idx += 1
    for k, (cpath, cstart, cmax) in enumerate(clips or []):
        inputs += ["-i", str(cpath)]
        ms = int(max(0.0, cstart) * 1000)
        filt.append(f"[{idx}:a]aformat=channel_layouts=stereo,atrim=0:{max(0.1, cmax):.3f},adelay={ms}|{ms},volume={clip_db}dB[c{k}]")
        labels.append(f"[c{k}]"); idx += 1
    if not labels:
        raise SystemExit("Nothing to mix (no voice, music or sfx).")
    filt.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0:duration=longest,atrim=0:{duration},loudnorm=I={lufs}:TP=-1.5:LRA=9[out]")
    run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(filt), "-map", "[out]", "-ar", "48000", str(out)])
    I, TP = loudness(out)
    log(f"mix -> {Path(out).name}: {I} LUFS, true peak {TP} dBFS")
    return out


WM_POS = {  # watermark corner -> overlay x:y expressions (m = margin in px)
    "br": "W-w-{m}:H-h-{m}", "bl": "{m}:H-h-{m}", "tr": "W-w-{m}:{m}", "tl": "{m}:{m}", "center": "(W-w)/2:(H-h)/2",
}


def output_size(width, height, max_short=None):
    """Downscale so the short side is at most max_short px (720 -> 1280x720 or 720x1280). Even dimensions."""
    if not max_short or min(width, height) <= max_short:
        return int(width), int(height)
    k = max_short / min(width, height)
    w, h = int(round(width * k)), int(round(height * k))
    return w - w % 2, h - h % 2


def mux(video, audio, out, watermark=None, watermark_pos="br", watermark_opacity=0.6, watermark_scale=0.18, max_height=None, size=None):
    """Mux picture + mix into an MP4. Optional PNG watermark overlay and a short-side cap (free plan).

    `max_height` caps the frame's short side ("720p" semantics for both portrait and landscape).
    `size` is the (w, h) of `video`; probed when omitted.
    """
    if size is None:
        size = probe_size(video)
    W, H = size
    ow, oh = output_size(W, H, max_height)
    filters, inputs = [], ["-i", str(video), "-i", str(audio)]
    label = "0:v"
    if (ow, oh) != (W, H):
        filters.append(f"[{label}]scale={ow}:{oh}:flags=lanczos[scaled]"); label = "scaled"
    if watermark:
        wm = Path(watermark)
        if not wm.exists():
            raise FileNotFoundError(f"watermark not found: {wm}")
        inputs += ["-i", str(wm)]
        margin = max(8, int(round(min(ow, oh) * 0.03)))
        wm_w = max(16, int(round(min(ow, oh) * float(watermark_scale))))
        pos = WM_POS.get(watermark_pos, WM_POS["br"]).format(m=margin)
        filters.append(f"[2:v]format=rgba,scale={wm_w}:-1:flags=lanczos,colorchannelmixer=aa={float(watermark_opacity)}[wm]")
        filters.append(f"[{label}][wm]overlay={pos}:format=auto[marked]"); label = "marked"
    cmd = ["ffmpeg", "-y", "-v", "error", *inputs]
    if filters:
        cmd += ["-filter_complex", ";".join(filters), "-map", f"[{label}]", "-map", "1:a",
                "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p"]
    else:
        cmd += ["-map", "0:v", "-map", "1:a", "-c:v", "copy"]
    cmd += ["-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-shortest", str(out)]
    run(cmd)
    log(f"final -> {out}" + (f" ({ow}x{oh})" if (ow, oh) != (W, H) else "") + (" +watermark" if watermark else ""))
    return out, (ow, oh)


def probe_size(path):
    p = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)], capture=True)
    w, h = p.stdout.strip().split(",")[:2]
    return int(w), int(h)


def qa(job, final):
    """Objective checks a human editor would do before delivery."""
    rep = {"file": str(final)}
    p = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate:format=duration,size",
             "-of", "json", str(final)], capture=True)
    info = json.loads(p.stdout)
    v = next((s for s in info["streams"] if s["codec_type"] == "video"), {})
    rep.update({"width": v.get("width"), "height": v.get("height"), "fps": v.get("r_frame_rate"), "duration": float(info["format"]["duration"]),
                "size_mb": round(int(info["format"]["size"]) / 1e6, 2), "has_audio": has_audio_stream(final)})
    rep["lufs"], rep["true_peak"] = loudness(final) if rep["has_audio"] else (None, None)
    W, H = job.size
    # The expected delivery size differs from the requested one for drafts (render scale) and the free plan (max_height).
    exp = job.data.get("output_size") or [W, H]
    rep["expected_width"], rep["expected_height"] = int(exp[0]), int(exp[1])
    issues = []
    if (rep["width"], rep["height"]) != (int(exp[0]), int(exp[1])):
        issues.append(f"resolution {rep['width']}x{rep['height']} != expected {exp[0]}x{exp[1]}")
    if (int(exp[0]), int(exp[1])) != (W, H):
        rep["note"] = f"delivered at {exp[0]}x{exp[1]} (requested {W}x{H}; draft render or plan resolution cap)"
    if rep["lufs"] is not None and abs(rep["lufs"] - job.data.get("lufs", -14)) > 1.5:
        issues.append(f"loudness {rep['lufs']} LUFS is off target")
    if rep["true_peak"] is not None and rep["true_peak"] > -0.5:
        issues.append(f"true peak {rep['true_peak']} dBFS is too hot")
    # black / frozen frame scan
    bl = run(["ffmpeg", "-hide_banner", "-i", str(final), "-vf", "blackdetect=d=0.4:pix_th=0.06", "-an", "-f", "null", "-"], capture=True, check=False)
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", bl.stderr or "")
    if blacks:
        issues.append("black frames at " + ", ".join(f"{a}-{b}s" for a, b in blacks))
    rep["issues"] = issues
    # thumbnails at 10 points for a visual pass
    qa_dir = job.p("qa"); qa_dir.mkdir(exist_ok=True)
    n = 10; d = rep["duration"]
    frames = []
    for i in range(n):
        t = d * (i + 0.5) / n
        f = qa_dir / f"final_{i:02d}.jpg"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(final), "-frames:v", "1", "-vf", "scale=360:-2", str(f)])
        frames.append(f)
    try:
        from .render import contact_sheet
        contact_sheet(frames, qa_dir / "final_sheet.jpg", cols=5)
    except Exception:
        pass
    (qa_dir / "report.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    log("QA: " + ("OK" if not issues else "; ".join(issues)))
    log(f"QA sheet: {qa_dir / 'final_sheet.jpg'}  (look at it before delivering)")
    return rep
