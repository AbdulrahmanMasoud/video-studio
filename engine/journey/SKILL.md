---
name: journey
description: "Make a timeline / history / \"my journey\" / company story video: a track that draws itself while the camera travels from event to event, years and labels popping in on the voice, and milestone cards with a rolling year counter. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"journey\", asks for a timelines video, or describes this format."
---

# Journey: timelines

Deep teal with drifting dots, amber track and years, cream event cards.

**Best for:** Histories, career stories, product evolution, roadmaps.

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
   - Also for this template: Dates and events.

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template journey --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace natural --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. One `timeline` with 3–6 `events`, each `at` on the year/date word (vertical track in portrait, horizontal otherwise).
2. Use `milestone` for the big moment or present day.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `timeline` | `title`, `events` [{`year`, `label`, `at`}], `orientation` auto|vertical|horizontal |
| `milestone` | `from`, `year`, `title`, `text`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** none.

## 5. Look and sound defaults

Captions `pill` · music `cinematic` ·
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
      "type": "timeline",
      "start": 0,
      "title": "My journey",
      "events": [
        {
          "year": 2015,
          "label": "First line of code",
          "at": "w:1"
        },
        {
          "year": 2017,
          "label": "First job",
          "at": "w:10"
        },
        {
          "year": 2020,
          "label": "Started freelancing",
          "at": "w:20"
        },
        {
          "year": 2023,
          "label": "Launched my company",
          "at": "w:27"
        }
      ]
    },
    {
      "type": "milestone",
      "start": "w:34-0.1",
      "from": 2015,
      "year": 2026,
      "title": "1,000,000 users",
      "text": "And we're just getting started",
      "at": "w:34"
    }
  ],
  "music": {
    "mood": "cinematic"
  }
}
```
