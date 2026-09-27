#!/usr/bin/env python3
"""Video Studio CLI - one command per production step.

  python vt.py doctor                     check dependencies
  python vt.py setup                      install Python deps + headless Chromium
  python vt.py templates                  list installed templates
  python vt.py init JOB --template steps --lang en --size 9:16 [--platform tiktok] [--input voice.m4a]
  python vt.py transcribe JOB             word-level transcript -> transcript.txt
  python vt.py tts JOB --text-file script.txt        (optional AI voice when there is no recording)
  python vt.py analyze JOB                speech map, pauses, retake candidates
  python vt.py edit JOB --pace tight --drop "w:40-w:43" --sections "12,57"
  python vt.py media JOB --name cam --video cam_edit.mp4 | --image logo.png
  python vt.py stills JOB --auto          preview frames + contact sheet (fast)
  python vt.py build JOB                  render + sfx + music + mix + mux + QA
  (render / sfx / music / mix / mux / qa also exist as single steps)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from vtlib.common import (PLATFORMS, SIZE_PRESETS, SKILLS_DIR, Job, die, has_video_stream, load_json, log, parse_size, run,  # noqa: E402
                          save_json, which)

REQ = ["numpy", "scipy", "soundfile", "PIL", "playwright", "faster_whisper"]


def cmd_doctor(a):
    ok = True
    for m in REQ:
        found = importlib.util.find_spec(m) is not None
        print(f"  {'ok ' if found else 'MISSING'}  python module {m}")
        ok &= found
    for b in ("ffmpeg", "ffprobe"):
        print(f"  {'ok ' if which(b) else 'MISSING'}  {b}")
        ok &= bool(which(b))
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(); b.close()
        print("  ok   headless chromium")
    except Exception as e:
        print(f"  MISSING headless chromium ({str(e).splitlines()[0][:80]})"); ok = False
    print("  optional: edge-tts " + ("ok" if importlib.util.find_spec("edge_tts") else "not installed (only needed for AI voiceover)"))
    print("ALL GOOD" if ok else "Run: python vt.py setup   (and install ffmpeg with your OS package manager)")
    return 0 if ok else 1


def cmd_setup(a):
    req = Path(__file__).resolve().parent / "requirements.txt"
    extra = ["--break-system-packages"] if a.break_system_packages else []
    run([sys.executable, "-m", "pip", "install", "-q", "-r", str(req), *extra], quiet=False)
    run([sys.executable, "-m", "playwright", "install", "chromium"], quiet=False)
    if not which("ffmpeg"):
        log("ffmpeg not found. Install it: macOS 'brew install ffmpeg', Ubuntu 'sudo apt install ffmpeg', Windows 'winget install ffmpeg'.")
    if a.model:
        from faster_whisper import WhisperModel
        WhisperModel(a.model, device="cpu", compute_type="int8"); log(f"whisper model {a.model} cached")
    return cmd_doctor(a)


def cmd_templates(a):
    for d in sorted(SKILLS_DIR.iterdir()):
        m = load_json(d / "template.json")
        if m:
            print(f"  {d.name:<14} {m.get('category',''):<18} {m.get('summary','')}")


def cmd_init(a):
    missing = [n for n, v in (("--template", a.template), ("--lang", a.lang), ("--size", a.size)) if not v]
    if missing:
        die("missing " + ", ".join(missing) + ". Ask the user for the video language and the dimensions/aspect ratio before starting "
            f"(size presets: {', '.join(sorted(SIZE_PRESETS))}, or WxH, or a ratio like 9:16).")
    W, H = parse_size(a.size)
    job = Job(a.job); job.dir.mkdir(parents=True, exist_ok=True)
    job.data.update({"template": a.template, "lang": a.lang, "width": W, "height": H, "fps": a.fps, "platform": a.platform,
                     "lufs": a.lufs, "numerals": a.numerals})
    if a.dir:
        job.data["dir"] = a.dir
    if a.input:
        src = Path(a.input).resolve()
        if not src.exists():
            die(f"input not found: {src}")
        job.data["input"] = str(src)
        job.data["input_kind"] = "video" if has_video_stream(src) else "audio"
    if a.captions:
        job.data["captions"] = {"style": a.captions}
    brand = {}
    if a.palette:
        brand["palette"] = json.loads(a.palette)
    if a.fonts:
        brand["fonts"] = json.loads(a.fonts)
    if brand:
        job.data["brand"] = brand
    job.template_dir()
    job.save()
    log(f"job ready: {job.dir}  ({a.template}, {a.lang}, {W}x{H}@{a.fps}, {a.platform})")


def cmd_transcribe(a):
    from vtlib.transcribe import transcribe
    job = Job(a.job)
    if not job.data.get("input"):
        die("this job has no --input audio/video. Use 'tts' for a generated voice, or plan a no-voice video.")
    transcribe(Path(job.data["input"]), a.lang or job.data.get("lang"), a.model, a.prompt, job.p("words.json"), job.p("transcript.txt"))


def cmd_tts(a):
    from vtlib.tts import synthesize
    job = Job(a.job)
    synthesize(job, Path(a.text_file).read_text(encoding="utf-8"), a.voice, a.rate)


def cmd_analyze(a):
    from vtlib.edit import analyze
    analyze(Job(a.job))


def cmd_edit(a):
    from vtlib.edit import build
    job = Job(a.job)
    sections = [int(x) for x in a.sections.replace(" ", "").split(",") if x] if a.sections else []
    build(job, pace=a.pace, drops=a.drop, section_words=sections, voice_lufs=a.voice_lufs)


def cmd_media(a):
    from vtlib.media import add_image, add_video
    job = Job(a.job)
    if a.image:
        add_image(job, a.name, a.image, a.fit)
    else:
        src = a.video or (job.p("cam_edit.mp4") if job.p("cam_edit.mp4").exists() else job.data.get("input"))
        if not src:
            die("give --video or --image")
        add_video(job, a.name, src, a.fit, a.box, None, a.start, a.duration)


def cmd_render(a):
    from vtlib.render import render
    job = Job(a.job)
    render(job, a.workers, 0.5 if a.draft else a.scale, a.out, a.start, a.end)


def cmd_stills(a):
    from vtlib.render import render
    job = Job(a.job)
    render(job, 1, a.scale, None, None, None, "auto" if a.auto or not a.times else a.times.split(","))


def _duration(job):
    d = job.data.get("duration")
    if not d:
        die("render first (duration unknown)")
    return float(d)


def cmd_sfx(a):
    from vtlib.sfx import build_track
    job = Job(a.job)
    cues = load_json(job.p("cues.json"), [])
    extra = (load_json(job.p("plan.json"), {}) or {}).get("sfx", [])
    words = job.words()
    for c in extra:  # manual cues in plan.json may use w:<index>
        if isinstance(c.get("t"), str) and c["t"].startswith("w"):
            i = int(c["t"].split(":")[1].split("+")[0].split("-")[0]); c["t"] = words[i]["s"] + (float(c["t"].split("+")[1]) if "+" in c["t"] else 0)
    unknown = build_track(cues + extra, _duration(job), job.p("sfx.wav"), a.gain)
    log(f"sfx: {len(cues) + len(extra)} cues -> sfx.wav" + (f" (unknown names skipped: {unknown})" if unknown else ""))


def _t(v, words):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    v = str(v)
    if v.startswith("w:"):
        return words[int(v[2:])]["s"]
    return float(v)


def cmd_music(a):
    from vtlib.music import MOODS, compose
    from vtlib.mix import prepare_music_file
    job = Job(a.job)
    plan = load_json(job.p("plan.json"), {}) or {}
    man = load_json(job.template_dir() / "template.json", {}) or {}
    cfg = dict(man.get("music", {})); cfg.update(plan.get("music", {}) or {})
    if a.none or cfg.get("mood") == "none":
        job.p("music.wav").unlink(missing_ok=True); log("music disabled"); return
    dur = _duration(job)
    f = a.file or cfg.get("file")
    if f:
        prepare_music_file(f, dur, job.p("music.wav")); log(f"music: user track {f}"); return
    words = job.words()
    mood = a.mood or cfg.get("mood", "lofi")
    if mood not in MOODS:
        die(f"unknown mood '{mood}'. Moods: {', '.join(MOODS)}")
    drop = _t(a.drop or cfg.get("drop"), words)
    end = _t(a.end or cfg.get("end"), words)
    stops = []
    for s in (a.stops.split(",") if a.stops else cfg.get("stops", [])):
        x, y = str(s).split("~") if "~" in str(s) else str(s).rsplit("-", 1)
        stops.append((_t(x, words), _t(y, words)))
    compose(dur, mood, a.bpm or cfg.get("bpm"), drop, stops, end, cfg.get("seed", 3), cfg.get("transpose", 0), job.p("music.wav"))
    log(f"music: {mood} {dur:.1f}s (drop {drop}, end {end})")


def cmd_mix(a):
    from vtlib.mix import mix
    job = Job(a.job)
    plan = load_json(job.p("plan.json"), {}) or {}
    mcfg = plan.get("mix", {})
    voice = job.voice()
    music = job.p("music.wav") if job.p("music.wav").exists() else None
    sfx = job.p("sfx.wav") if job.p("sfx.wav").exists() else None
    mix(voice, music, sfx, _duration(job), job.p("mix.wav"), job.data.get("lufs", -14),
        a.music_db if a.music_db is not None else mcfg.get("music_db", -13 if voice else -8),
        a.sfx_db if a.sfx_db is not None else mcfg.get("sfx_db", 2), not a.no_duck)


def cmd_mux(a):
    from vtlib.mix import mux
    job = Job(a.job)
    out = Path(a.out) if a.out else job.p(job.data.get("output", "final.mp4"))
    mux(job.p("video_noaudio.mp4"), job.p("mix.wav"), out)
    job.data["final"] = str(out); job.save()


def cmd_qa(a):
    from vtlib.mix import qa
    job = Job(a.job)
    qa(job, Path(job.data.get("final") or job.p("final.mp4")))


def cmd_build(a):
    a.gain = 0.0; a.mood = None; a.bpm = None; a.drop = None; a.end = None; a.stops = None; a.file = None
    a.music_db = None; a.sfx_db = None; a.no_duck = False; a.none = a.no_music
    cmd_render(a); cmd_sfx(a); cmd_music(a); cmd_mix(a); cmd_mux(a); cmd_qa(a)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("doctor"); s.set_defaults(fn=cmd_doctor)
    s = sp.add_parser("setup"); s.add_argument("--model", default=None, help="pre-download a whisper model (e.g. medium)")
    s.add_argument("--break-system-packages", action="store_true"); s.set_defaults(fn=cmd_setup)
    s = sp.add_parser("templates"); s.set_defaults(fn=cmd_templates)
    s = sp.add_parser("init"); s.add_argument("job"); s.add_argument("--template"); s.add_argument("--lang"); s.add_argument("--size")
    s.add_argument("--platform", default="none", choices=PLATFORMS); s.add_argument("--fps", type=int, default=30); s.add_argument("--input")
    s.add_argument("--lufs", type=float, default=-14.0); s.add_argument("--numerals", default="auto", choices=["auto", "latin", "native"])
    s.add_argument("--dir", choices=["ltr", "rtl"]); s.add_argument("--captions", help="pill|karaoke|pop|line|boxed|none")
    s.add_argument("--palette", help='JSON brand colors, e.g. {"bg":"#101820","accent":"#FEE715"}'); s.add_argument("--fonts", help='JSON, e.g. {"display":"Sora"}')
    s.set_defaults(fn=cmd_init)
    s = sp.add_parser("transcribe"); s.add_argument("job"); s.add_argument("--model", default="medium"); s.add_argument("--lang"); s.add_argument("--prompt")
    s.set_defaults(fn=cmd_transcribe)
    s = sp.add_parser("tts"); s.add_argument("job"); s.add_argument("--text-file", required=True); s.add_argument("--voice"); s.add_argument("--rate", default="+0%")
    s.set_defaults(fn=cmd_tts)
    s = sp.add_parser("analyze"); s.add_argument("job"); s.set_defaults(fn=cmd_analyze)
    s = sp.add_parser("edit"); s.add_argument("job"); s.add_argument("--pace", default="tight", choices=["tight", "natural", "relaxed", "none"])
    s.add_argument("--drop", help="ranges to remove: 'w:12-w:15,31.2-32.0'"); s.add_argument("--sections", help="word indices that start a new section")
    s.add_argument("--voice-lufs", type=float, default=-16.0); s.set_defaults(fn=cmd_edit)
    s = sp.add_parser("media"); s.add_argument("job"); s.add_argument("--name", required=True); s.add_argument("--video"); s.add_argument("--image")
    s.add_argument("--fit", default="cover", choices=["cover", "contain"]); s.add_argument("--box"); s.add_argument("--start", type=float, default=0.0)
    s.add_argument("--duration", type=float); s.set_defaults(fn=cmd_media)
    for name, fn in (("render", cmd_render), ("build", cmd_build)):
        s = sp.add_parser(name); s.add_argument("job"); s.add_argument("--workers", type=int); s.add_argument("--draft", action="store_true")
        s.add_argument("--scale", type=float, default=1.0); s.add_argument("--out"); s.add_argument("--start", type=float); s.add_argument("--end", type=float)
        if name == "build":
            s.add_argument("--no-music", action="store_true")
        s.set_defaults(fn=fn)
    s = sp.add_parser("stills"); s.add_argument("job"); s.add_argument("--times"); s.add_argument("--auto", action="store_true")
    s.add_argument("--scale", type=float, default=0.5); s.set_defaults(fn=cmd_stills)
    s = sp.add_parser("sfx"); s.add_argument("job"); s.add_argument("--gain", type=float, default=0.0); s.set_defaults(fn=cmd_sfx)
    s = sp.add_parser("music"); s.add_argument("job"); s.add_argument("--mood"); s.add_argument("--bpm", type=float); s.add_argument("--drop")
    s.add_argument("--end"); s.add_argument("--stops"); s.add_argument("--file"); s.add_argument("--none", action="store_true"); s.set_defaults(fn=cmd_music)
    s = sp.add_parser("mix"); s.add_argument("job"); s.add_argument("--music-db", type=float); s.add_argument("--sfx-db", type=float)
    s.add_argument("--no-duck", action="store_true"); s.set_defaults(fn=cmd_mix)
    s = sp.add_parser("mux"); s.add_argument("job"); s.add_argument("--out"); s.set_defaults(fn=cmd_mux)
    s = sp.add_parser("qa"); s.add_argument("job"); s.set_defaults(fn=cmd_qa)
    a = ap.parse_args()
    r = a.fn(a)
    sys.exit(r if isinstance(r, int) else 0)


if __name__ == "__main__":
    main()
