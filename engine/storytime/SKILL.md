---
name: storytime
description: "Edit a personal story / storytime / life-lesson video: warm color-graded footage (or voice-only), chapter title cards, polaroid photos that drop in, handwritten notes and a closing card. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"storytime\", asks for a personal stories video, or describes this format."
---

# Storytime: personal stories

Warm film grade and light leaks, serif chapter cards, polaroids with tape, karaoke captions in amber.

**Best for:** Narrative content: "the day I…", journeys, lessons, confessions.

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
   - Also for this template: Camera video or voice; any photos to include.

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template storytime --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace natural --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

**Media:** `cam` (optional), photos by name. Register with `vt.py media JOB --name <name> --video <file>` or `--image <file>`. Without media the template draws a clean placeholder, so previews still work.

## 3. Storyboard rules

1. Break the story into 2–4 `chapter`s; `hold` controls how long the card covers the footage.
2. Between chapters use `talk` (optionally with a short handwritten `note`).
3. Drop a `photo` when the story mentions a person/place/object (register with `media --image`).
4. End with `end` (the lesson in ≤ 5 words).

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `chapter` | `n`, `kicker`, `title`, `at`, `hold` |
| `talk` | `note`, `noteAt`, `noteEnd` |
| `photo` | `media`, `caption`, `at`, `end`, `rotate` |
| `end` | `text`, `sub`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** `chapter`, `end`.

## 5. Look and sound defaults

Captions `karaoke` · music `piano` ·
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
      "type": "chapter",
      "start": 0,
      "n": 1,
      "title": "The day I quit",
      "at": 0.1,
      "hold": "w:10"
    },
    {
      "type": "talk",
      "start": "w:10-0.05",
      "note": "“You're crazy.”",
      "noteAt": "w:15"
    }
  ],
  "music": {
    "mood": "piano",
    "drop": "w:37"
  }
}
```
