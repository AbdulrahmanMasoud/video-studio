"""Dialogue editing: find speech, remove silences/breaths/bad takes, clean the voice, remap word timings.

The same edit decision list (EDL) is applied to a camera video when the source is a video,
so picture and sound stay in sync.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from .common import has_video_stream, load_json, log, run, save_json
from .transcribe import write_indexed

SR = 48000
HOP = 0.01


def decode(src, dst, sr=SR):
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", str(sr), "-c:a", "pcm_s16le", str(dst)])
    return dst


def read_wav(p):
    import soundfile as sf
    a, sr = sf.read(str(p), dtype="float32", always_2d=False)
    if a.ndim > 1:
        a = a.mean(axis=1)
    return a, sr


def write_wav(p, a, sr=SR):
    import soundfile as sf
    sf.write(str(p), a.astype(np.float32), sr)


def rms_db(a, sr, hop=HOP):
    h = int(sr * hop)
    n = len(a) // h
    if n == 0:
        return np.array([-120.0])
    fr = a[: n * h].reshape(n, h)
    return 20 * np.log10(np.sqrt((fr ** 2).mean(axis=1)) + 1e-9)


def find_speech(a, sr, merge_gap=0.14, min_len=0.06):
    e = rms_db(a, sr)
    floor = float(np.percentile(e, 10))
    p95 = float(np.percentile(e, 95))
    thr = max(floor + 16, p95 - 30)
    sp = e > thr
    segs, s = [], None
    for i, v in enumerate(sp):
        if v and s is None:
            s = i
        if not v and s is not None:
            segs.append([s, i]); s = None
    if s is not None:
        segs.append([s, len(sp)])
    merged = []
    for s, t in segs:
        if merged and (s - merged[-1][1]) * HOP < merge_gap:
            merged[-1][1] = t
        else:
            merged.append([s, t])
    out = []
    for s, t in merged:
        dur = (t - s) * HOP
        lvl = float(e[s:t].mean())
        if dur < min_len:
            continue
        if dur < 0.35 and lvl < thr + 6:      # clicks, lip smacks, short breaths
            continue
        out.append({"s": round(s * HOP, 3), "e": round(t * HOP, 3), "db": round(lvl, 1)})
    return out, {"floor_db": round(floor, 1), "p95_db": round(p95, 1), "threshold_db": round(thr, 1)}


def stumble_candidates(words):
    """Heuristics that flag likely retakes: repeated words/phrases close together, and low-confidence fragments."""
    c = []
    norm = lambda s: re.sub(r"[^\w]", "", s.lower())
    for i in range(1, len(words)):
        a, b = norm(words[i - 1]["w"]), norm(words[i]["w"])
        if a and a == b and words[i]["s"] - words[i - 1]["e"] < 1.5:
            c.append({"type": "repeated-word", "words": [i - 1, i], "text": words[i]["w"], "t": words[i - 1]["s"]})
    for n in (2, 3, 4):
        for i in range(len(words) - 2 * n + 1):
            x = [norm(w["w"]) for w in words[i:i + n]]
            for j in range(i + n, min(len(words) - n + 1, i + n + 6)):
                y = [norm(w["w"]) for w in words[j:j + n]]
                if x == y and all(x) and words[j]["s"] - words[i]["s"] < 6:
                    c.append({"type": f"repeated-{n}gram", "words": [i, j + n - 1], "text": " ".join(w["w"] for w in words[i:i + n]), "t": words[i]["s"]})
    for i, w in enumerate(words):
        if w.get("p", 1) < 0.35 and len(norm(w["w"])) <= 2:
            c.append({"type": "low-confidence-fragment", "words": [i, i], "text": w["w"], "t": w["s"]})
    seen, out = set(), []
    for x in c:
        k = (x["type"], tuple(x["words"]))
        if k not in seen:
            seen.add(k); out.append(x)
    return out


def analyze(job):
    src = Path(job.data["input"])
    raw = job.p("voice_raw.wav")
    if not raw.exists():
        decode(src, raw)
    a, sr = read_wav(raw)
    segs, stats = find_speech(a, sr)
    clip = float((np.abs(a) > 0.985).mean())
    stats.update({"duration": round(len(a) / sr, 2), "clipped_ratio": round(clip, 5), "speech_seconds": round(sum(s["e"] - s["s"] for s in segs), 2)})
    save_json(job.p("segments.json"), {"stats": stats, "segments": segs})
    words = load_json(job.p("words.json")) or []
    cands = stumble_candidates(words) if words else []
    save_json(job.p("stumbles.json"), cands)
    lines = [f"duration {stats['duration']}s, speech {stats['speech_seconds']}s, noise floor {stats['floor_db']} dB, clipped {clip*100:.2f}%",
             f"{len(segs)} speech segments. Pauses longer than 0.6s: " + ", ".join(f"{segs[i]['e']:.2f}-{segs[i+1]['s']:.2f}" for i in range(len(segs) - 1) if segs[i + 1]['s'] - segs[i]['e'] > 0.6)]
    if segs and segs[0]["s"] > 1.0:
        lines.append(f"Leading non-speech before {segs[0]['s']:.2f}s will be removed.")
    if cands:
        lines.append("Possible retakes / stumbles (review against the transcript, then pass --drop):")
        for x in cands[:40]:
            lines.append(f"  - {x['type']}: words {x['words'][0]}..{x['words'][1]} '{x['text']}' at {x['t']:.2f}s")
    else:
        lines.append("No automatic retake candidates. Still read transcript.txt for false starts.")
    if clip > 0.001:
        lines.append("Clipping detected: declipping will be applied during edit.")
    (job.p("analysis.txt")).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return segs


def parse_drops(spec: str | None, words):
    """'w:12-w:15, 31.2-32.0' -> [(a,b), ...] in source seconds."""
    out = []
    if not spec:
        return out
    for part in re.split(r"[,;]", spec):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"^w:(\d+)\s*-\s*w:(\d+)$", part)
        if m:
            i, j = int(m.group(1)), int(m.group(2))
            i, j = min(i, j), max(i, j)
            a = words[i]["s"] - 0.02
            b = words[j]["e"] + 0.02 if j + 1 >= len(words) else min(words[j]["e"] + 0.02, words[j + 1]["s"] - 0.01)
            out.append((a, b)); continue
        m = re.match(r"^(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)$", part)
        if m:
            out.append((float(m.group(1)), float(m.group(2)))); continue
        raise ValueError(f"Bad --drop item '{part}'. Use w:START-w:END (word indices) or SECONDS-SECONDS.")
    return out


PACES = {  # (within phrase, between phrases, between sentences, section break)
    "tight": (0.10, 0.18, 0.28, 0.42),
    "natural": (0.18, 0.30, 0.45, 0.60),
    "relaxed": (0.25, 0.45, 0.70, 0.90),
}


def build(job, pace="tight", drops=None, section_words=None, lead=0.3, tail=0.35, voice_lufs=-16.0, keep_breaths=False):
    words = load_json(job.p("words.json")) or []
    segd = load_json(job.p("segments.json"))
    if not segd:
        analyze(job); segd = load_json(job.p("segments.json"))
    segs = [(s["s"], s["e"]) for s in segd["segments"]]
    raw = job.p("voice_raw.wav")
    a, sr = read_wav(raw)
    clipped = segd["stats"].get("clipped_ratio", 0) > 0.001

    # 1) remove dropped ranges from speech segments
    for (da, db) in parse_drops(drops, words) if isinstance(drops, str) or drops is None else drops:
        nxt = []
        for s, e in segs:
            if e <= da or s >= db:
                nxt.append((s, e))
            else:
                if s < da - 0.05:
                    nxt.append((s, da))
                if e > db + 0.05:
                    nxt.append((db, e))
        segs = nxt
    if pace == "none":
        segs = [(max(0, segs[0][0] - 0.1), segs[-1][1] + 0.1)] if segs else []

    # 2) choose gap lengths
    within, phrase, sentence, section = PACES.get(pace, PACES["tight"])
    sec_times = []
    for w in section_words or []:
        if 0 <= w < len(words):
            sec_times.append(words[w]["s"])
    ends_sentence = set()
    for w in words:
        if w["w"][-1:] in ".!?؟。！？":
            ends_sentence.add(round(w["e"], 2))
    PRE, POST = 0.03, 0.07
    out, edl, cur = [np.zeros(int(lead * sr), np.float32)], [], lead
    fade_n = int(0.008 * sr)
    for i, (s, e) in enumerate(segs):
        if i > 0:
            g = s - segs[i - 1][1]
            if any(abs(s - st) < 0.25 or (segs[i - 1][1] <= st <= s + 0.05) for st in sec_times):
                ng = section
            elif g >= 0.7 or any(abs(segs[i - 1][1] - x) < 0.3 for x in ends_sentence):
                ng = sentence
            elif g >= 0.3:
                ng = phrase
            else:
                ng = min(g, within)
            ng = max(ng - PRE - POST, 0.02)
            out.append(np.zeros(int(ng * sr), np.float32)); cur += ng
        s0 = max(0.0, s - PRE)
        e0 = e + POST
        if i + 1 < len(segs):
            e0 = min(e0, segs[i + 1][0] - PRE)
        seg = a[int(s0 * sr): int(e0 * sr)].copy()
        if len(seg) > 2 * fade_n:
            ramp = np.linspace(0, 1, fade_n, dtype=np.float32)
            seg[:fade_n] *= ramp; seg[-fade_n:] *= ramp[::-1]
        edl.append({"src_start": round(s0, 4), "src_end": round(s0 + len(seg) / sr, 4), "dst_start": round(cur, 4)})
        out.append(seg); cur += len(seg) / sr
    out.append(np.zeros(int(tail * sr), np.float32))
    y = np.concatenate(out) if out else np.zeros(sr, np.float32)
    cut = job.p("voice_cut.wav")
    write_wav(cut, y, sr)

    # 3) voice processing chain (broadcast-style)
    chain = ["adeclip"] if clipped else []
    chain += ["highpass=f=75", "equalizer=f=220:t=q:w=1.2:g=-2", "equalizer=f=3200:t=q:w=1.4:g=2.2", "equalizer=f=10000:t=h:w=0.7:g=1.2",
              "deesser=i=0.3", "acompressor=threshold=-20dB:ratio=3:attack=4:release=90:makeup=2",
              f"loudnorm=I={voice_lufs}:TP=-1.5:LRA=7"]
    run(["ffmpeg", "-y", "-v", "error", "-i", str(cut), "-af", ",".join(chain), "-ar", str(SR), "-ac", "1", str(job.p("voice_edit.wav"))])

    # 4) remap words
    def mp(t):
        for x in edl:
            if x["src_start"] - 1e-3 <= t <= x["src_end"] + 1e-3:
                return x["dst_start"] + (t - x["src_start"])
        return None
    new = []
    for i, w in enumerate(words):
        mid = (w["s"] + w["e"]) / 2
        s = mp(w["s"]) if mp(w["s"]) is not None else mp(mid)
        if s is None:
            continue  # the word was cut away (retake/drop)
        e = mp(w["e"])
        if e is None:
            e = s + max(0.08, min(w["e"] - w["s"], 0.6))
        new.append({"w": w["w"], "s": round(s, 3), "e": round(max(e, s + 0.05), 3), "src": i, "p": w.get("p", 1)})
    for i in range(len(new) - 1):
        new[i]["e"] = min(new[i]["e"], new[i + 1]["s"])
    save_json(job.p("words_edit.json"), new)
    write_indexed(new, job.p("transcript_edit.txt"), job.data.get("lang"))
    save_json(job.p("edl.json"), {"segments": edl, "duration": round(cur + tail, 3), "pace": pace})
    job.data["voice"] = str(job.p("voice_edit.wav")); job.data["duration_hint"] = round(cur + tail, 3); job.save()
    log(f"edited voice: {round(len(a)/sr,1)}s -> {round(cur + tail,1)}s  ({len(edl)} segments, {len(words) - len(new)} words removed)")
    log("next: read transcript_edit.txt (indices changed!) and write plan.json using w:<index> anchors")

    # 5) cut the camera video with the same EDL
    src = Path(job.data["input"])
    if has_video_stream(src) and job.data.get("input_kind") == "video":
        cut_video(src, edl, job.p("cam_edit.mp4"), lead, tail)
    return new


def cut_video(src, edl, dst, lead, tail):
    """Trim+concat the picture with the EDL (no audio; the mix supplies audio)."""
    parts, filt = [], []
    # freeze-frame lead-in/tail keep picture length equal to the audio
    for i, x in enumerate(edl):
        filt.append(f"[0:v]trim=start={x['src_start']}:end={x['src_end']},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[v{i}]")
    filt.append(f"{''.join(parts)}concat=n={len(parts)}:v=1:a=0[cat]")
    filt.append(f"[cat]tpad=start_duration={lead}:start_mode=clone:stop_duration={tail}:stop_mode=clone[out]")
    script = Path(dst).with_suffix(".filter.txt")
    script.write_text(";\n".join(filt), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-filter_complex_script", str(script), "-map", "[out]", "-an",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", str(dst)])
    log(f"camera cut with EDL -> {Path(dst).name}")
