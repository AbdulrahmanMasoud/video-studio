#!/usr/bin/env python3
"""Generate engine/<template>/SKILL.md from engine-dev/skilldata.py + each template.json.

Run after changing skilldata.py:  python3 engine-dev/gen_skills.py
"""
import json
from pathlib import Path

from skilldata import T

ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / "engine"


def example_snippet(name):
    f = SK / name / "examples" / "plan.example.json"
    if not f.exists():
        return ""
    plan = json.loads(f.read_text(encoding="utf-8"))
    plan.pop("demoScript", None)
    plan.pop("demoMedia", None)
    scenes = plan.get("scenes", [])[:2]
    short = {"lang": plan.get("lang", "en"), "scenes": scenes}
    if plan.get("music"):
        short["music"] = plan["music"]
    if plan.get("data"):
        short["data"] = plan["data"]
    return json.dumps(short, ensure_ascii=False, indent=2)


def render(name, d):
    m = json.loads((SK / name / "template.json").read_text(encoding="utf-8"))
    desc = (d["desc"] + " Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); "
            "asks for the language and dimensions if they were not given. Use when the user says \""
            + name + "\", asks for a " + d["tag"] + " video, or describes this format.")
    scenes = "\n".join(f"| `{k}` | {v} |" for k, v in d["scenes"])
    rules = "\n".join(f"{i}. {r}" for i, r in enumerate(d["rules"], 1))
    labels = ", ".join(f"`{x}`" for x in d.get("labels", [])) or "none"
    media = d.get("media")
    media_md = ("\n**Media:** " + "; ".join(media) + ". Register with `vt.py media JOB --name <name> --video <file>` or `--image <file>`. "
                "Without media the template draws a clean placeholder, so previews still work.\n") if media else ""
    data_md = f"\n**Template data:** {d['data']}\n" if d.get("data") else ""
    ar = "\nAn Arabic (RTL) example is in `examples/plan.ar.json`." if (SK / name / "examples" / "plan.ar.json").exists() else ""
    extra = f"\n   - Also for this template: {d['extra_intake']}" if d.get("extra_intake") else ""
    return f"""---
name: {name}
description: {json.dumps(desc, ensure_ascii=False)}
---

# {d['title']}: {d['tag']}

{d['look']}

**Best for:** {d['when']}

This skill is a template for the Video Studio engine. The engine (`video-engine`, a sibling folder of
this skill) does transcription, editing, rendering, sound design and mixing. Its `SKILL.md` has the
full pipeline; the essentials are repeated here.

## 1. Intake (do this first)

Before producing anything, make sure you know these two things. **If the user has not told you,
ask them in one short message and wait for the answer:**

- **Language** of the video (spoken and on-screen text).
- **Dimensions**: `9:16` (TikTok/Reels/Shorts), `1:1`, `4:5`, `16:9` (YouTube) or a custom `WIDTHxHEIGHT`.

Then confirm or sensibly assume (and say what you assumed):
   - Source: voice recording, camera video, script for an AI voice, or no voice.
   - Platform (for safe zones), target length, brand colors, music preference.{extra}

## 2. Produce

```bash
VT="python3 ${{CLAUDE_SKILL_DIR}}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template {name} --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace {d.get('pace', 'tight')} --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```
{media_md}
## 3. Storyboard rules

{rules}

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
{scenes}
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.
{data_md}
**Translatable labels:** {labels}.

## 5. Look and sound defaults

Captions `{m.get('captions', {}).get('style', 'pill')}` · music `{m.get('music', {}).get('mood', 'lofi')}` ·
palette keys can be overridden in the plan (`"palette": {{"accent": "#..."}}`) or with `init --palette`.
Sound effects are placed automatically on every reveal.

## Example

A complete example (with the script it was written for) is in `examples/plan.example.json`.{ar}
First scenes:

```json
{example_snippet(name)}
```
"""


def main():
    for name, d in T.items():
        (SK / name / "SKILL.md").write_text(render(name, d), encoding="utf-8")
        desc_len = len(render(name, d).split("description: ", 1)[1].split("\n", 1)[0])
        print(f"{name:14} description {desc_len} chars")


if __name__ == "__main__":
    main()
