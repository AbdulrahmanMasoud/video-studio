---
name: quiz
description: "Create an interactive quiz / trivia / \"guess the answer\" video: question card, A-D options that pop in on the voice, a countdown ring with ticks, and a green reveal of the correct answer, plus an explanation card and a score screen. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"quiz\", asks for a question, options, countdown and reveal video, or describes this format."
---

# Quiz: question, options, countdown and reveal

Violet gradient with drifting question marks, white cards, a yellow countdown ring that turns red, and a satisfying correct/incorrect reveal.

**Best for:** Trivia, test-your-knowledge, "can you guess", educational checks.

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
   - Also for this template: The correct answer for each question (confirm if the script doesn't say it).

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template quiz --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. One `question` per question; anchor each option's `at` to the word that says it.
2. `countdownAt` on the "3, 2, 1" (or leave a 2–3 s pause); `revealAt` on the word that gives the answer.
3. Follow with `explain` (why) and optionally end with `score`.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `question` | `q`, `options` [{`text`, `at`}] or strings, `answer` (0-based index), `at`, `optionsAt`, `countdownAt`, `seconds` (3), `revealAt`, `countdown` (false to hide), `label` |
| `explain` | `title`, `text`, `icon`, `at` |
| `score` | `total`, `score`, `text`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** `question`, `letters (option letters, e.g. "أبجد")`, `why`, `score`.

## 5. Look and sound defaults

Captions `pill` · music `game` ·
palette keys can be overridden in the plan (`"palette": {"accent": "#..."}`) or with `init --palette`.
Sound effects are placed automatically on every reveal.

## Example

A complete example (with the script it was written for) is in `examples/plan.example.json`.
An Arabic (RTL) example is in `examples/plan.ar.json`.
First scenes:

```json
{
  "lang": "en",
  "scenes": [
    {
      "type": "question",
      "start": 0,
      "at": "w:2",
      "q": "Which planet is the hottest?",
      "options": [
        {
          "text": "Mercury",
          "at": "w:13"
        },
        {
          "text": "Venus",
          "at": "w:14"
        },
        {
          "text": "Mars",
          "at": "w:15"
        },
        {
          "text": "Jupiter",
          "at": "w:17"
        }
      ],
      "answer": 1,
      "countdownAt": "w:22",
      "seconds": 3,
      "revealAt": "w:25"
    },
    {
      "type": "explain",
      "start": "w:27-0.1",
      "title": "Thick atmosphere",
      "text": "Venus is farther from the Sun than Mercury, but its CO2 blanket traps the heat: about 465°C.",
      "at": "w:27",
      "icon": "fire"
    }
  ],
  "music": {
    "mood": "game"
  }
}
```
