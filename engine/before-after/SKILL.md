---
name: before-after
description: "Make a before/after transformation video (makeover, redesign, room/desk setup, fitness progress, code refactor, photo edit): a wipe slider reveals the after image or clip, or two cards compare bullet points side by side. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"before-after\", asks for a transformations with a wipe reveal video, or describes this format."
---

# Before / After: transformations with a wipe reveal

Dark frame, red BEFORE / green AFTER chips, a white divider with a handle that teases, then sweeps across.

**Best for:** Anything with a clear before state and after state.

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
   - Platform (for safe zones), target length, brand colors, music preference.
   - Also for this template: The before and after images/clips (or the list of differences if there are no images).

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template before-after --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

**Media:** before/after images or clips (any names). Register with `vt.py media JOB --name <name> --video <file>` or `--image <file>`. Without media the template draws a clean placeholder, so previews still work.

## 3. Storyboard rules

1. Register the images/clips first: `vt.py media JOB --name before_img --image before.jpg` and `--name after_img …`.
2. `compare` with `wipeAt` on the word that introduces the result ("here's the after").
3. Follow with `split` to list what changed (anchor `afterAt` to the first change).

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `compare` | `before` {`label`, `media`, `items`, `text`}, `after` {…}, `at`, `wipeAt`, `wipeDur`, `full` (edge-to-edge) |
| `split` | `before` {`label`, `items`}, `after` {…}, `at`, `afterAt` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** `before`, `after`.

## 5. Look and sound defaults

Captions `pill` · music `upbeat` ·
palette keys can be overridden in the plan (`"palette": {"accent": "#..."}`) or with `init --palette`.
Sound effects are placed automatically on every reveal.

## Example

A complete example (with the script it was written for) is in `examples/plan.example.json`.
First scenes:

```json
{
  "lang": "en",
  "scenes": [
    {
      "type": "compare",
      "start": 0,
      "at": 0.1,
      "wipeAt": "w:20",
      "before": {
        "label": "BEFORE",
        "media": "before_img"
      },
      "after": {
        "label": "AFTER",
        "media": "after_img"
      }
    },
    {
      "type": "split",
      "start": "w:33-0.1",
      "at": "w:33",
      "afterAt": "w:36",
      "before": {
        "label": "BEFORE",
        "items": [
          "Cables everywhere",
          "No light",
          "Can't focus"
        ]
      },
      "after": {
        "label": "AFTER",
        "items": [
          "Cable tray",
          "One lamp",
          "Monitor arm"
        ]
      }
    }
  ],
  "music": {
    "mood": "upbeat"
  }
}
```
