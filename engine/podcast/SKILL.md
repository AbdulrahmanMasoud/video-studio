---
name: podcast
description: "Turn a podcast, interview or conversation into a vertical or landscape clip: split speaker panels (video or avatars) that light up on whoever is talking, live audio meters, an ON AIR badge with the show name, pull-quote cards and solo views. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"podcast\", asks for a podcast / interview clips video, or describes this format."
---

# Podcast: podcast / interview clips

Dark studio, rounded speaker panels with a red active-speaker ring, boxed captions, show badge on top.

**Best for:** Two or three people talking; interview or podcast highlights.

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
   - Also for this template: Speaker names (and roles), who speaks when (or let transcription + listening decide), show name, per-speaker footage if any.

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template podcast --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace natural --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

**Media:** one video per speaker (optional), e.g. `--name host`, `--name guest`. Register with `vt.py media JOB --name <name> --video <file>` or `--image <file>`. Without media the template draws a clean placeholder, so previews still work.

## 3. Storyboard rules

1. Put speakers in `data.speakers` [{`name`, `role`, `media`}] and the show name in `data.show`.
2. Use `split` with `turns` [{`who`, `start`, `end`}] covering who talks when (anchor to words).
3. Cut to `quote` for the most shareable sentence; `solo` for a long answer by one speaker.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `split` | `speakers` (else `data.speakers`), `turns` [{`who`, `start`, `end`}], `speaker` (default active) |
| `solo` | `who`, `media` |
| `quote` | `text`, `who`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Template data:** `data.speakers`, `data.show`, `data.badge`.

**Translatable labels:** `onair`.

## 5. Look and sound defaults

Captions `boxed` · music `none` ·
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
      "type": "split",
      "start": 0,
      "turns": [
        {
          "who": 0,
          "start": 0,
          "end": "we:7+0.15"
        },
        {
          "who": 1,
          "start": "w:8-0.1",
          "end": "we:24+0.15"
        },
        {
          "who": 0,
          "start": "w:25-0.1",
          "end": "we:34+0.15"
        },
        {
          "who": 1,
          "start": "w:35-0.1",
          "end": 999
        }
      ]
    },
    {
      "type": "quote",
      "start": "w:36-0.1",
      "text": "Talk to ten customers before you write one line of code.",
      "who": "Lina, Founder of Nodebox",
      "at": "w:36"
    }
  ],
  "music": {
    "mood": "none"
  },
  "data": {
    "show": "The Build Show",
    "speakers": [
      {
        "name": "Omar",
        "role": "Host"
      },
      {
        "name": "Lina",
        "role": "Founder, Nodebox"
      }
    ]
  }
}
```
