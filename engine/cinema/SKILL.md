---
name: cinema
description: "Make a cinematic trailer / documentary / brand film video: letterbox bars, film grain and vignette, elegant serif titles that breathe open, Ken Burns motion on photos and clips, roman-numeral chapter cards and a closing title. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"cinema\", asks for a trailer & documentary look video, or describes this format."
---

# Cinema: trailer & documentary look

Black and warm gold, serif typography, subtitle-style captions, cinematic music with a boom on titles.

**Best for:** Storytelling with footage/photos, brand films, trailers, travel films.

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
   - Also for this template: The footage/photos to use (b-roll), title of the film.

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template cinema --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace relaxed --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

**Media:** b-roll clips/photos by name. Register with `vt.py media JOB --name <name> --video <file>` or `--image <file>`. Without media the template draws a clean placeholder, so previews still work.

## 3. Storyboard rules

1. Register every clip/photo (`media --name shot1 --video …`).
2. Alternate `shot` scenes (3–6 s each) with sparse `title`/`chapter` cards; end with `end`.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `title` | `kicker`, `text`, `sub`, `at`, `upper` |
| `shot` | `media`, `text`, `at`, `kenburns` {`from`, `to`, `x`, `y`}, `mediaOffset` |
| `chapter` | `n`, `numeral` (arabic for 1,2,3), `title`, `at` |
| `end` | `text`, `sub`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** none.

## 5. Look and sound defaults

Captions `line` · music `cinematic` ·
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
      "kicker": "A SHORT FILM",
      "text": "The First Light",
      "at": 0.4
    },
    {
      "type": "shot",
      "start": "w:5-0.2",
      "media": "shot1",
      "kenburns": {
        "from": 1.02,
        "to": 1.15,
        "x": 0.4,
        "y": 0.4
      }
    }
  ],
  "music": {
    "mood": "cinematic"
  }
}
```
