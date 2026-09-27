---
name: screen
description: "Turn a screen recording into a polished app / website / SaaS walkthrough: the recording inside a browser or phone frame, an animated cursor that glides to each click, click ripples, callout labels and camera zooms, plus numbered step cards. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"screen\", asks for a app & website walkthroughs video, or describes this format."
---

# Screen Demo: app & website walkthroughs

Light lavender background, realistic browser chrome or phone bezel, dark callout labels, indigo accents.

**Best for:** Product demos, feature tours, onboarding, how-to-use-this-app.

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
   - Also for this template: The screen recording (or screenshots) and where the important clicks are.

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template screen --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace natural --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

**Media:** `screen` (the recording or a screenshot). Register with `vt.py media JOB --name <name> --video <file>` or `--image <file>`. Without media the template draws a clean placeholder, so previews still work.

## 3. Storyboard rules

1. Register the recording: `vt.py media JOB --name screen --video rec.mp4` (`mediaOffset` to skip).
2. Clicks use `x`/`y` as fractions of the screen (0–1). Anchor `at` to the word describing the action.
3. Insert `step` cards between parts of a longer demo.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `demo` | `device` browser|phone|none, `media` (screen), `url`, `title`, `ratio`, `clicks` [{`x`, `y`, `at`, `end`, `label`, `zoom` (1.3)}], `mediaOffset` |
| `step` | `n`, `text`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** none.

## 5. Look and sound defaults

Captions `pill` · music `corporate` ·
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
      "type": "step",
      "start": 0,
      "n": 1,
      "text": "Your first project in 30 seconds",
      "at": 0.1
    },
    {
      "type": "demo",
      "start": "w:11-0.4",
      "device": "browser",
      "url": "app.example.com/projects",
      "clicks": [
        {
          "x": 0.85,
          "y": 0.06,
          "at": "w:11",
          "label": "New project",
          "end": "we:17"
        },
        {
          "x": 0.4,
          "y": 0.45,
          "at": "w:21",
          "label": "Name it",
          "end": "we:25",
          "zoom": 1.4
        },
        {
          "x": 0.78,
          "y": 0.9,
          "at": "w:28",
          "label": "Create",
          "end": "we:35"
        }
      ]
    }
  ],
  "music": {
    "mood": "corporate"
  }
}
```
