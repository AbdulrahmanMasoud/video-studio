---
name: hot-take
description: "Make a hot take / unpopular opinion / controversial statement video built for comments: fiery kicker, words that slam in one by one, a live poll with animated bars, and a comment call-to-action. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"hot-take\", asks for a bold opinions video, or describes this format."
---

# Hot Take: bold opinions

Near-black with rising embers and diagonal stripes, huge uppercase statement with highlighted words, one-word pop captions.

**Best for:** Opinions, debates, "unpopular opinion", engagement bait done tastefully.

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

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template hot-take --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. `take` for the statement (≤ 8 words, `highlight` 1–2 words). A second `take` can give the reason.
2. `poll` with plausible percentages the user provides (label them as illustrative if invented).
3. End with `cta` inviting comments.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `take` | `kicker`, `text`, `highlight` [words], `at`, `stagger`, `upper` |
| `poll` | `question`, `options` [{`label`, `pct`, `at`}], `at`, `fillAt` |
| `cta` | `text`, `sub`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** `kicker`, `cta`, `ctaSub`.

## 5. Look and sound defaults

Captions `pop` · music `edm` ·
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
      "type": "take",
      "start": 0,
      "kicker": "Unpopular opinion",
      "text": "Morning routines are overrated",
      "highlight": [
        "overrated"
      ],
      "at": "w:2"
    },
    {
      "type": "take",
      "start": "w:17-0.1",
      "kicker": "What matters",
      "text": "Your best hours, whenever they are",
      "highlight": [
        "best",
        "hours"
      ],
      "at": "w:17"
    }
  ],
  "music": {
    "mood": "edm",
    "drop": "w:2"
  }
}
```
