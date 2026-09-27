"""Render plan.json with a template into frames and encode them (headless Chromium + ffmpeg)."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import time
from pathlib import Path

from .common import RUNTIME_DIR, die, load_json, log, progress, run, save_json, warn
from .fonts import resolve_fonts
from .media import audio_levels


def build_config(job, plan=None):
    tdir = job.template_dir()
    manifest = load_json(tdir / "template.json", {}) or {}
    plan = plan or load_json(job.p("plan.json"))
    if not plan:
        die(f"No plan.json in {job.dir}. Write the storyboard first (see the template's SKILL.md).")
    W, H = job.size
    lang = plan.get("lang") or job.data.get("lang") or "en"
    words = plan.get("words") if plan.get("words") is not None else job.words()
    caps = dict(manifest.get("captions", {}))
    caps.update(job.data.get("captions", {}) or {})
    caps.update(plan.get("captions", {}) or {})
    roles = manifest.get("fonts", ["display", "body"])
    css, stacks = resolve_fonts(lang, roles, (job.data.get("brand") or {}).get("fonts"))
    palette = dict((job.data.get("brand") or {}).get("palette") or {})
    palette.update(plan.get("palette") or {})
    voice = job.voice()
    fps = job.data.get("fps", 30)
    cfg = {
        "width": W, "height": H, "fps": fps, "lang": lang, "dir": plan.get("dir") or job.data.get("dir"),
        "platform": job.data.get("platform", "none"), "words": words, "scenes": plan.get("scenes", []),
        "captions": caps, "palette": palette, "labels": plan.get("labels", {}), "data": plan.get("data", {}),
        "media": job.data.get("media", {}), "fonts": stacks, "numerals": plan.get("numerals", job.data.get("numerals", "auto")),
        "duration": plan.get("duration") or job.data.get("duration_hint"),
        "levels": audio_levels(voice, fps) if voice else [], "levelsFps": fps,
        # edit points (seconds, edited timeline) so talking-head templates can punch in on jump cuts
        "cuts": plan.get("cuts") if plan.get("cuts") is not None else [x["dst_start"] for x in ((load_json(job.p("edl.json"), {}) or {}).get("segments") or [])[1:]],
    }
    return cfg, css, tdir


def write_page(job, css, tdir):
    shell = (RUNTIME_DIR / "shell.html").read_text(encoding="utf-8")
    html = (shell.replace("/*__FONT_CSS__*/", css)
            .replace("__ENGINE__", (RUNTIME_DIR / "engine.js").resolve().as_uri())
            .replace("__TEMPLATE__", (tdir / "template.js").resolve().as_uri()))
    d = job.p("render"); d.mkdir(exist_ok=True)
    page = d / "page.html"
    page.write_text(html, encoding="utf-8")
    return page


async def _open(browser, page_file, cfg, scale):
    pg = await browser.new_page(viewport={"width": cfg["width"], "height": cfg["height"]}, device_scale_factor=scale)
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    await pg.goto(page_file.resolve().as_uri())
    try:
        info = await pg.evaluate("cfg => window.__init(cfg)", cfg)
    except Exception as e:
        raise RuntimeError(f"Template failed to initialise: {e}\n" + "\n".join(errors[-5:]))
    return pg, info, errors


def _encoder(out, fps, crf=17):
    return subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(fps), "-c:v", "mjpeg", "-i", "-",
                             "-c:v", "libx264", "-preset", "medium", "-crf", str(crf), "-pix_fmt", "yuv420p", "-r", str(fps), str(out)],
                            stdin=subprocess.PIPE)


async def _render_range(browser, page_file, cfg, scale, f0, f1, out, fps, label):
    pg, info, errors = await _open(browser, page_file, cfg, scale)
    enc = _encoder(out, fps)
    t0 = time.time()
    for i in range(f0, f1):
        await pg.evaluate("t => window.__frame(t)", i / fps)
        buf = await pg.screenshot(type="jpeg", quality=93, clip={"x": 0, "y": 0, "width": cfg["width"], "height": cfg["height"]})
        enc.stdin.write(buf)
        if (i - f0) % 150 == 0:
            el = time.time() - t0
            progress("render", (i - f0) / max(1, f1 - f0), f"{label}: frame {i - f0}/{f1 - f0}  ({(i - f0) / el if el > 0 else 0:.1f} fps)", worker=label)
    enc.stdin.close(); enc.wait()
    await pg.close()
    if errors:
        warn(f"{label}: browser reported: " + " | ".join(errors[-3:]), browser_errors=len(errors))


async def _main(job, workers, scale, out, start, end, stills):
    from playwright.async_api import async_playwright
    cfg, css, tdir = build_config(job)
    page_file = write_page(job, css, tdir)
    async with async_playwright() as p:
        browser = await p.chromium.launch(args=["--allow-file-access-from-files", "--disable-web-security", "--font-render-hinting=none", "--disable-gpu"])
        pg, info, errors = await _open(browser, page_file, cfg, scale)
        if errors:
            warn("browser: " + " | ".join(errors[-5:]), browser_errors=len(errors))
        save_json(job.p("cues.json"), info["cues"])
        save_json(job.p("render/scenes.json"), info["scenes"])
        for w in info.get("warnings", []):
            warn(w)
        dur, fps = info["duration"], cfg["fps"]
        job.data["duration"] = dur
        if stills is None:
            job.data["render_scale"] = scale
            job.data["output_size"] = [int(cfg["width"] * scale), int(cfg["height"] * scale)]
        job.save()
        if stills is not None:
            qa = job.p("qa"); qa.mkdir(exist_ok=True)
            if stills == "auto":
                ts = []
                for s in info["scenes"]:
                    ts.append(round(s["start"] + max(0.4, (s["end"] - s["start"]) * 0.72), 2))
                ts = ts or [dur / 2]
            else:
                ts = [float(x) for x in stills]
            files = []
            for t in ts:
                await pg.evaluate("t => window.__frame(t)", t)
                f = qa / f"still_{t:07.2f}.png"
                await pg.screenshot(path=str(f), clip={"x": 0, "y": 0, "width": cfg["width"], "height": cfg["height"]})
                files.append(f)
            await browser.close()
            contact_sheet(files, qa / "contact_sheet.jpg")
            log(f"{len(files)} stills + contact sheet in {qa}")
            return
        await pg.close()
        n = int(round(dur * fps))
        f0 = int(round((start or 0) * fps)); f1 = min(n, int(round(end * fps)) if end else n)
        workers = max(1, min(workers, (f1 - f0) // 30 or 1))
        step = (f1 - f0 + workers - 1) // workers
        parts, tasks = [], []
        for k in range(workers):
            a, b = f0 + k * step, min(f1, f0 + (k + 1) * step)
            if a >= b:
                continue
            part = job.p(f"render/part_{k:02d}.mp4"); parts.append(part)
            tasks.append(_render_range(browser, page_file, cfg, scale, a, b, part, fps, f"worker {k + 1}/{workers}"))
        log(f"rendering {f1 - f0} frames ({(f1 - f0) / fps:.1f}s) at {int(cfg['width'] * scale)}x{int(cfg['height'] * scale)} with {len(tasks)} worker(s)")
        await asyncio.gather(*tasks)
        await browser.close()
    lst = job.p("render/parts.txt")
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)])
    progress("render", 1.0, f"video (no audio) -> {out}")


def render(job, workers=None, scale=1.0, out=None, start=None, end=None, stills=None):
    workers = workers or max(1, min(4, (os.cpu_count() or 2)))
    out = Path(out or job.p("video_noaudio.mp4"))
    asyncio.run(_main(job, workers, scale, out, start, end, stills))
    return out


def contact_sheet(files, out, cols=4, thumb_w=360):
    from PIL import Image
    ims = [Image.open(f).convert("RGB") for f in files]
    if not ims:
        return
    r = ims[0].height / ims[0].width
    tw, th = thumb_w, int(thumb_w * r)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 8) + 8, rows * (th + 8) + 8), (240, 240, 240))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((tw, th)), (8 + (i % cols) * (tw + 8), 8 + (i // cols) * (th + 8)))
    sheet.save(out, quality=85)
