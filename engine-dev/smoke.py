#!/usr/bin/env python3
"""Developer smoke test: render preview stills for templates at several sizes using example plans.

python engine-dev/smoke.py [template ...] [--sizes 9:16,1:1,16:9] [--lang-plan ar]
Words are synthesized from the example plan's "demoScript" so no audio is needed.
"""
import argparse, json, re, subprocess, sys, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / "engine"
VT = SK / "video-engine/scripts/vt.py"

def words_from(script):
    t, out = 0.35, []
    for tok in script.split():
        out.append({"w": tok, "s": round(t, 3), "e": round(t + 0.28, 3)})
        t += 0.32 + (0.35 if re.search(r"[.!?؟,،]$", tok) else 0)
    return out

def demo_media(out, kind, size):
    """Synthetic footage (ffmpeg test pattern) so media code paths get exercised."""
    w, h = {"9:16": (540, 960), "1:1": (720, 720), "16:9": (960, 540)}.get(size, (720, 720))
    f = out / (f"_demo_{kind}_{w}x{h}." + ("jpg" if kind == "image" else "mp4"))
    if not f.exists():
        src = f"testsrc2=size={w}x{h}:rate=30" if kind != "image" else f"gradients=size={w}x{h}:seed=3"
        args = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", src] + (["-frames:v", "1"] if kind == "image" else ["-t", "20", "-pix_fmt", "yuv420p"]) + [str(f)]
        subprocess.run(args, check=True)
    return f

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("templates", nargs="*"); ap.add_argument("--sizes", default="9:16,1:1,16:9")
    ap.add_argument("--plan", default="plan.example.json"); ap.add_argument("--out", default=str(ROOT / "engine-dev/_smoke"))
    ap.add_argument("--times", default="auto")
    a = ap.parse_args()
    names = a.templates or sorted(d.name for d in SK.iterdir() if (d / "template.js").exists())
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    bad = []
    for n in names:
        plan_f = SK / n / "examples" / a.plan
        if not plan_f.exists():
            print("skip (no example)", n); continue
        plan = json.loads(plan_f.read_text())
        for size in a.sizes.split(","):
            job = out / f"{n}_{size.replace(':','x')}"
            if job.exists(): shutil.rmtree(job)
            r = subprocess.run([sys.executable, str(VT), "init", str(job), "--template", n, "--lang", plan.get("lang", "en"), "--size", size, "--platform", plan.get("platform", "tiktok")], capture_output=True, text=True)
            if r.returncode: print(r.stderr); bad.append(n); continue
            for name, kind in (plan.get("demoMedia") or {}).items():
                src = demo_media(out, kind, size)
                subprocess.run([sys.executable, str(VT), "media", str(job), "--name", name, "--" + ("image" if kind == "image" else "video"), str(src)], capture_output=True, text=True, check=True)
            p = dict(plan); p["words"] = words_from(plan.get("demoScript", "")); p.pop("demoScript", None); p.pop("demoMedia", None)
            if not p["words"]: p["duration"] = plan.get("duration", 8)
            (job / "plan.json").write_text(json.dumps(p, ensure_ascii=False))
            args = [sys.executable, str(VT), "stills", str(job), "--scale", "0.4"] + (["--auto"] if a.times == "auto" else ["--times", a.times])
            r = subprocess.run(args, capture_output=True, text=True)
            msg = (r.stdout + r.stderr)
            errs = [l for l in msg.splitlines() if "browser" in l or "Error" in l or "error" in l.lower()]
            status = "FAIL" if r.returncode or errs else "ok"
            if status == "FAIL": bad.append(f"{n}@{size}")
            print(f"{status:4} {n:14} {size:6} " + (" | ".join(errs)[:400] if errs else ""))
            if r.returncode: print(msg[-1500:])
            sheet = job / "qa/contact_sheet.jpg"
            if sheet.exists(): shutil.copy(sheet, out / f"sheet_{n}_{size.replace(':','x')}.jpg")
    print("FAILED:", bad if bad else "none")
    sys.exit(1 if bad else 0)

if __name__ == "__main__": main()
