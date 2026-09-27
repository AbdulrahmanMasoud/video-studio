---
name: counter
description: "Create a data / statistics video where numbers count up on the voice: giant animated figures with rings or bar charts, labels and sources, and animated comparison bars. For facts, research findings, growth, reports. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"counter\", asks for a numbers & data stories video, or describes this format."
---

# Counter: numbers & data stories

Deep navy with a cyan grid glow, tabular numbers, cyan-to-lime bars.

**Best for:** Any script built around numbers.

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
   - Also for this template: The real figures and their sources (never invent statistics; mark examples as illustrative).

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template counter --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. One `stat` per headline number, `at` on the number word; `chart` ring for percentages, bars for growth.
2. `compare` for 2–5 values side by side.
3. Add `source` whenever the number comes from a study.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `stat` | `value`, `prefix`, `suffix`, `decimals`, `label`, `sub`, `source`, `chart` none|ring|bars, `max` (ring), `bars` [values], `at`, `dur` |
| `compare` | `title`, `items` [{`label`, `value`, `prefix`, `suffix`, `decimals`, `highlight`, `at`}], `at` |
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
      "type": "stat",
      "start": 0,
      "value": 91,
      "suffix": "%",
      "chart": "ring",
      "max": 100,
      "label": "quit a new habit",
      "sub": "within the first month",
      "at": "w:6",
      "dur": 1.6,
      "source": "Illustrative data"
    },
    {
      "type": "stat",
      "start": "w:20-0.1",
      "value": 3,
      "suffix": "×",
      "chart": "bars",
      "bars": [
        1,
        1.2,
        1.6,
        2.1,
        3
      ],
      "label": "more likely to stick with it",
      "at": "w:31",
      "dur": 1.2
    }
  ],
  "music": {
    "mood": "corporate",
    "drop": "w:6"
  }
}
```
