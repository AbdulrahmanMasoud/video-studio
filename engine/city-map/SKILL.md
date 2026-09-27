---
name: city-map
description: "Make a travel / city guide / itinerary / \"best places in X\" video: a stylized animated city map with pins dropping in as each place is named, a route that draws itself between them, and place cards with photos and star ratings. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"city-map\", asks for a travel & places video, or describes this format."
---

# City Map: travel & places

Clean light map (roads, parks, a river) generated per video, red pins, blue dashed route, white cards.

**Best for:** Travel guides, food tours, day plans, store locations.

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
   - Also for this template: The places in order, ratings, photos (optional).

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template city-map --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace natural --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. `map` with 2–5 `pins`; `x`/`y` (0–1) roughly reflect real relative positions.
2. `routeAt` after the last pin to reveal the route.
3. One `place` card per highlight.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `map` | `title`, `pins` [{`label`, `x`, `y`, `at`}], `routeAt`, `routeDur`, `seed`, `zoom` |
| `place` | `name`, `tag`, `rating`, `text`, `media`, `icon`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** none.

## 5. Look and sound defaults

Captions `pill` · music `acoustic` ·
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
      "type": "map",
      "start": 0,
      "title": "One day in Lisbon",
      "seed": 11,
      "pins": [
        {
          "label": "Alfama café",
          "x": 0.75,
          "y": 0.25,
          "at": "w:7"
        },
        {
          "label": "Time Out Market",
          "x": 0.3,
          "y": 0.6,
          "at": "w:16"
        },
        {
          "label": "Miradouro",
          "x": 0.55,
          "y": 0.85,
          "at": "w:24"
        }
      ],
      "routeAt": "w:24+0.8",
      "routeDur": 1.6
    },
    {
      "type": "place",
      "start": "w:28-0.1",
      "name": "Miradouro da Senhora do Monte",
      "tag": "SUNSET",
      "rating": 4.8,
      "text": "The best view in the city. Get there 30 minutes early.",
      "at": "w:28"
    }
  ],
  "music": {
    "mood": "acoustic"
  }
}
```
