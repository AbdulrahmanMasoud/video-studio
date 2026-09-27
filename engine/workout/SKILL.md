---
name: workout
description: "Make a workout / exercise / fitness routine video: exercise cards with a live rep counter synced to the counting voice or an interval countdown ring, rest timers with \"next up\", and a trophy finish with confetti. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"workout\", asks for a fitness routines video, or describes this format."
---

# Workout: fitness routines

Black with neon-lime streaks, huge rep numbers, pink rest ring, workout music.

**Best for:** Home workouts, gym routines, stretching, challenges.

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
   - Also for this template: Exercises, reps or seconds, sets, rest times, demo footage (optional).

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template workout --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. For reps, set `repTimes` to the counted words ("one, two…") so the counter follows the voice.
2. Use `seconds` for timed holds; `rest` between exercises; `done` at the end.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `exercise` | `name`, `set`, `reps`, `repTimes` [times], `repEvery`, `seconds`, `media`, `at` |
| `rest` | `seconds`, `next`, `label`, `at` |
| `done` | `text`, `sub`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** `reps`, `sec`, `rest`, `next`, `done`.

## 5. Look and sound defaults

Captions `pill` · music `workout` ·
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
      "type": "exercise",
      "start": 0,
      "name": "Squats",
      "set": "SET 1 / 3",
      "reps": 10,
      "repTimes": [
        "w:3",
        "w:4",
        "w:5",
        "w:6",
        "w:7",
        "w:8",
        "w:9",
        "w:10",
        "w:11",
        "w:12"
      ],
      "at": "w:2"
    },
    {
      "type": "rest",
      "start": "w:13-0.1",
      "seconds": 15,
      "next": "Plank",
      "at": "w:14"
    }
  ],
  "music": {
    "mood": "workout"
  }
}
```
