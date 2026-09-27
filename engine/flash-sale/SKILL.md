---
name: flash-sale
description: "Make a flash sale / discount / limited-time offer promo video: a shaking giant percentage, a live countdown clock, product tiles with slashed prices and a dashed promo-code box. Works with or without a voiceover. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"flash-sale\", asks for a loud promos video, or describes this format."
---

# Flash Sale: loud promos

Hot red with a spinning sunburst and scrolling yellow SALE tapes, EDM beat.

**Best for:** Discounts, Black Friday, launches with deadlines.

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
   - Also for this template: Discount, deadline, products and prices, promo code. Voiceover or music-only?

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template flash-sale --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. Music-only version: no `--input`, set `"duration"` (8–15 s) and use seconds for times.
2. `sale` first; `items` if there are products; `cta` with the code last.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `sale` | `kicker`, `value`, `prefix`, `suffix` (%), `word` (OFF), `timer` {`seconds`}, `fine`, `at` |
| `items` | `items` [{`name`, `price`, `old`, `media`, `icon`, `at`}], `currency`, `at` |
| `cta` | `text`, `code`, `sub`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Template data:** `data.tape` sets the scrolling tape text.

**Translatable labels:** `flash`, `off`, `cta`.

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
      "type": "sale",
      "start": 0,
      "kicker": "FLASH SALE",
      "value": 50,
      "suffix": "%",
      "at": "w:4",
      "timer": {
        "seconds": 86400
      },
      "fine": "Ends in 24 hours. While stocks last."
    },
    {
      "type": "items",
      "start": "w:15-0.1",
      "currency": "$",
      "items": [
        {
          "name": "Sneakers",
          "price": 45,
          "old": 90,
          "at": "w:15"
        },
        {
          "name": "Hoodie",
          "price": 30,
          "old": 60,
          "at": "w:16"
        },
        {
          "name": "Backpack",
          "price": 25,
          "old": 50,
          "at": "w:17"
        },
        {
          "name": "Cap",
          "price": 10,
          "old": 20,
          "at": "w:18"
        }
      ]
    }
  ],
  "music": {
    "mood": "edm",
    "drop": "w:4"
  },
  "data": {
    "tape": "FLASH SALE • 50% OFF • 24H ONLY • "
  }
}
```
