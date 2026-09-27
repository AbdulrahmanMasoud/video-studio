#!/usr/bin/env python3
"""End-to-end engine check without any LLM: espeak-ng voice -> transcribe -> edit -> simple plan -> stills -> build.

    python3 engine-dev/e2e_build.py /jobs/smoke [--template steps] [--model small] [--draft] [--size 9:16]

The plan is a minimal `steps` storyboard anchored to the real word indices of transcript_edit.txt
(hook on the first sentence, one step per following sentence, outro on the last one). It exists to
prove the CLI contract inside Docker; the product's fallback planner lives in apps/worker.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VT = ROOT / "engine/video-engine/scripts/vt.py"
SCRIPT = ("Here are three tips for better sleep. First, keep a fixed bedtime every night. "
          "Second, put your phone away one hour before bed. Third, keep the room cool and dark. Sleep well.")


def vt(*args, check=True):
    cmd = [sys.executable, str(VT), *map(str, args)]
    print("+", " ".join(cmd[1:]), flush=True)
    r = subprocess.run(cmd, text=True)
    if check and r.returncode:
        sys.exit(f"vt.py {args[0]} failed with exit code {r.returncode}")
    return r.returncode


def sentences(words):
    """Split edited words into sentences by punctuation -> list of (first_index, last_index)."""
    out, start = [], 0
    for i, w in enumerate(words):
        if re.search(r"[.!?؟]$", w["w"]) or i == len(words) - 1:
            out.append((start, i)); start = i + 1
    return out


def make_plan(words):
    sents = sentences(words)
    if len(sents) < 3:
        sents = [(0, len(words) // 3), (len(words) // 3 + 1, 2 * len(words) // 3), (2 * len(words) // 3 + 1, len(words) - 1)]
    def title(a, b, max_len=40):
        out = []
        for w in words[a:b + 1]:
            if len(" ".join(out + [w["w"]])) > max_len:
                break
            out.append(w["w"])
        return " ".join(out or [words[a]["w"]]).rstrip(" .,")
    scenes = [{"type": "hook", "start": 0, "title": title(*sents[0]), "icon": "bulb", "at": f"w:{sents[0][0]}"}]
    body = sents[1:-1] or sents[1:]
    for k, (a, b) in enumerate(body, 1):
        scenes.append({"type": "step", "start": f"w:{a}-0.1", "short": words[a]["w"].strip(".,!?").title() or f"Tip {k}", "title": title(a, b),
                       "card": {"kind": "text", "text": title(a, b), "at": f"w:{min(a + 1, b)}"}})
    a, b = sents[-1]
    if len(sents) > 2:
        scenes.append({"type": "outro", "start": f"w:{a}-0.1", "label": "Remember", "text": title(a, b), "textAt": f"w:{a}", "cta": "Save this"})
    return {"lang": "en", "scenes": scenes, "music": {"mood": "lofi", "drop": f"w:{sents[0][1]}"}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("job"); ap.add_argument("--template", default="steps"); ap.add_argument("--model", default="small")
    ap.add_argument("--size", default="9:16"); ap.add_argument("--draft", action="store_true"); ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    job = Path(a.job); job.mkdir(parents=True, exist_ok=True)
    voice = job / "voice.wav"
    if not voice.exists():
        subprocess.run(["espeak-ng", "-v", "en-us", "-s", "150", "-w", str(voice), SCRIPT], check=True)
        print("+ espeak-ng ->", voice)
    vt("init", job, "--template", a.template, "--lang", a.lang, "--size", a.size, "--platform", "tiktok", "--input", voice)
    vt("transcribe", job, "--model", a.model)
    vt("analyze", job)
    vt("edit", job, "--pace", "tight")
    words = json.loads((job / "words_edit.json").read_text())
    print(f"+ {len(words)} words after edit")
    (job / "plan.json").write_text(json.dumps(make_plan(words), ensure_ascii=False, indent=2))
    vt("stills", job, "--auto")
    vt("build", job, *(["--draft"] if a.draft else []))
    rep = json.loads((job / "qa/report.json").read_text())
    print(json.dumps(rep, indent=2))
    ok = Path(rep["file"]).exists() and rep["has_audio"] and rep["lufs"] is not None
    print("E2E", "OK" if ok else "FAILED", "| issues:", rep["issues"] or "none")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
