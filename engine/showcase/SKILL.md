---
name: showcase
description: "Make a product ad / launch / promo video: the product floats on a lit pedestal, feature chips pop in, the price slams in with the old price struck out, and a tap-the-button CTA closes it. Works with a product photo (PNG cutout ideal) or a placeholder. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"showcase\", asks for a product ads video, or describes this format."
---

# Showcase: product ads

Warm studio white, soft glow, black price tag, orange accent, bright pop music.

**Best for:** E-commerce, launches, merch, apps, services.

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
   - Also for this template: Product name, price and currency, 2–4 features, product image, the CTA wording.

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template showcase --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

**Media:** `product` image (optional). Register with `vt.py media JOB --name <name> --video <file>` or `--image <file>`. Without media the template draws a clean placeholder, so previews still work.

## 3. Storyboard rules

1. Register the product image: `vt.py media JOB --name product --image product.png`.
2. `product` with `features` anchored to the words; `priceAt` on the price.
3. End with `cta` (button text in the video language).

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `product` | `name`, `tagline`, `media`, `badge`, `features` [{`text`, `at`, `icon`}], `price`, `oldPrice`, `currency`, `priceAt`, `at` |
| `cta` | `text`, `button`, `sub`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** `shop`.

## 5. Look and sound defaults

Captions `pill` · music `upbeat` ·
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
      "type": "product",
      "start": 0,
      "name": "Aura Bottle",
      "tagline": "The bottle that reminds you to drink",
      "badge": "NEW",
      "at": "w:0",
      "features": [
        {
          "text": "Glows to remind you",
          "at": "w:11",
          "icon": "bolt"
        },
        {
          "text": "Cold for 24h",
          "at": "w:18",
          "icon": "clock"
        },
        {
          "text": "Tracks in the app",
          "at": "w:26",
          "icon": "check"
        }
      ],
      "price": 39,
      "oldPrice": 59,
      "currency": "$",
      "priceAt": "w:35"
    },
    {
      "type": "cta",
      "start": "w:38-0.1",
      "text": "Get yours today",
      "button": "Shop now",
      "sub": "Free shipping this week",
      "at": "w:38"
    }
  ],
  "music": {
    "mood": "upbeat",
    "drop": "w:0"
  }
}
```
