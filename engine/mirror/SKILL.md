---
name: mirror
description: "Edit a talking-head / face-to-camera video like a pro creator: removes pauses and stumbles, punch-in zooms on every jump cut, one-word pop captions, emphasis zooms, sticker callouts, headline cards and lower-third name tags. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"mirror\", asks for a talking-head edit video, or describes this format."
---

# Mirror: talking-head edit

The user's footage full-frame with alternating 1.0×/1.12× punch-ins on each cut, big yellow pop captions, bold stickers and a clean white headline.

**Best for:** The user recorded themselves talking to camera.

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
   - Also for this template: The camera video (required). Whether they want their name/title shown.

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template mirror --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

**Media:** `cam` (the edited camera video: `vt.py media JOB --name cam`). Register with `vt.py media JOB --name <name> --video <file>` or `--image <file>`. Without media the template draws a clean placeholder, so previews still work.

## 3. Storyboard rules

1. `init --input video.mp4`, then `transcribe`, `analyze`, `edit` (cuts both audio and footage), then `vt.py media JOB --name cam`.
2. Split the video into `talk` scenes by idea. Add `zooms` (snap: true) on punchlines, `stickers` for key phrases (≤ 5 words).
3. Open with `title` over the first sentence; add `lower` once, early, if the speaker should be introduced.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `talk` | `zooms` [{`at`, `end`, `scale` (1.3), `x`, `y` (0–1 focus), `snap`}], `stickers` [{`text`, `at`, `end`, `icon`, `pos` top|middle, `color`}] |
| `title` | `text`, `sub`, `at`, `end` |
| `lower` | `name`, `role`, `at`, `end` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Template data:** `data.punch: false` disables automatic punch-ins; `data.cam` renames the camera media.

**Translatable labels:** none.

## 5. Look and sound defaults

Captions `pop` · music `lofi` ·
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
      "text": "Stop saying sorry",
      "sub": "Email tip #1",
      "at": 0.1,
      "end": "w:6"
    },
    {
      "type": "talk",
      "start": "w:6-0.05",
      "zooms": [
        {
          "at": "w:6",
          "end": "we:6+0.2",
          "scale": 1.35,
          "snap": true
        }
      ],
      "stickers": [
        {
          "text": "Sorry for the late reply",
          "icon": "x",
          "at": "w:7",
          "end": "we:15",
          "color": "alt"
        },
        {
          "text": "Thank you for your patience",
          "icon": "check",
          "at": "w:18",
          "end": "we:29"
        }
      ]
    }
  ],
  "music": {
    "mood": "lofi"
  }
}
```
