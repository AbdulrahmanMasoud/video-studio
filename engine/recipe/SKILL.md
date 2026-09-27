---
name: recipe
description: "Make a recipe / cooking / food video: a plated title card with time and servings, an ingredient checklist that ticks off, numbered step cards with a kitchen timer, and a final dish reveal with sparkles. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"recipe\", asks for a cooking videos video, or describes this format."
---

# Recipe: cooking videos

Cream kitchen check pattern, tomato-red accents, handwritten finish, jazzy music.

**Best for:** Recipes, drinks, meal prep, baking.

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
   - Also for this template: Ingredients with quantities, steps, cooking times, photos of steps/dish (optional).

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template recipe --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace natural --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. `title` first, `ingredients` next (quantities in `qty`).
2. One `step` per action; `timer` in seconds for waits.
3. End with `final`.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `title` | `text`, `time`, `servings`, `media`, `at` |
| `ingredients` | `title`, `items` [{`text`, `qty`, `at`}] |
| `step` | `n`, `text`, `timer` (seconds), `media`, `at` |
| `final` | `text`, `media`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** `ingredients`, `final`.

## 5. Look and sound defaults

Captions `pill` · music `jazzy` ·
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
      "type": "title",
      "start": 0,
      "text": "Garlic butter pasta",
      "time": "15 min",
      "servings": "2",
      "at": 0.2
    },
    {
      "type": "ingredients",
      "start": "w:6-0.1",
      "items": [
        {
          "text": "Pasta",
          "qty": "200 g",
          "at": "w:8"
        },
        {
          "text": "Butter",
          "qty": "3 tbsp",
          "at": "w:9"
        },
        {
          "text": "Garlic",
          "qty": "4 cloves",
          "at": "w:10"
        },
        {
          "text": "Parmesan",
          "qty": "50 g",
          "at": "w:11"
        },
        {
          "text": "Parsley",
          "qty": "a handful",
          "at": "w:13"
        }
      ]
    }
  ],
  "music": {
    "mood": "jazzy"
  }
}
```
