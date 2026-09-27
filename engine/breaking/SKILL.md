---
name: breaking
description: "Make a breaking-news / news-update / announcement video in TV style: flashing BREAKING banner, headline bar, media window, numbered key points, LIVE badge, channel name and a scrolling ticker. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"breaking\", asks for a news bulletins video, or describes this format."
---

# Breaking: news bulletins

Navy newsroom with red and white bars, news music and beeps, boxed captions.

**Best for:** News, updates, announcements, launches, recaps.

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
   - Also for this template: Headline, key points, channel name, an image or clip for the headline (optional).

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template breaking --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. `headline` first (title ≤ 10 words).
2. One `point` per key fact.
3. Ticker items in `data.ticker` (short).

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `headline` | `label`, `title`, `sub`, `media`, `icon`, `at` |
| `point` | `n`, `text`, `kicker`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Template data:** `data.channel`, `data.ticker` [strings], `data.tickerLabel`, `data.live`.

**Translatable labels:** `breaking`, `live`, `latest`.

## 5. Look and sound defaults

Captions `boxed` · music `news` ·
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
      "type": "headline",
      "start": 0,
      "label": "BREAKING NEWS",
      "title": "AI now edits full videos from a single voice note",
      "sub": "Here's what you need to know",
      "at": 0.2
    },
    {
      "type": "point",
      "start": "w:22-0.1",
      "text": "Works in any language",
      "kicker": "KEY POINT",
      "at": "w:22"
    }
  ],
  "music": {
    "mood": "news"
  },
  "data": {
    "channel": "TECH DAILY",
    "ticker": [
      "AI edits full videos from a voice note",
      "Works in any language",
      "Any aspect ratio",
      "Free to try today"
    ]
  }
}
```
