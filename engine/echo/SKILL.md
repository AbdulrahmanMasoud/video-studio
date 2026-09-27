---
name: echo
description: "Make a kinetic typography video where the spoken words themselves are the visuals: every word animates in exactly as it is said, lines resize to fill the frame, emphasized words explode in color. Ideal for motivational speeches, quotes, poetry and punchy statements. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"echo\", asks for a kinetic typography video, or describes this format."
---

# Echo: kinetic typography

Black with slow color glows, massive uppercase type, lime accent words, pink live-word highlight. No separate captions (the type is the caption).

**Best for:** Motivation, quotes, manifesto-style statements, voice-only content.

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
$VT init JOB --template echo --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace natural --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. `flow` does it automatically from the transcript: list 3–6 `emphasis` words.
2. Use `words` for a hand-crafted climax (styles: normal, accent, huge, small, outline, strike).
3. End with `quote` if there is a closing line or attribution.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `flow` | `emphasis` [words], `maxChars`, `lines`, `upper` |
| `words` | `items` [{`text`, `at`, `style`, `strikeAt`, `clear`}], `upper` |
| `quote` | `text`, `author`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** none.

## 5. Look and sound defaults

Captions `none` · music `cinematic` ·
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
      "type": "flow",
      "start": 0,
      "emphasis": [
        "nobody",
        "save",
        "luck"
      ]
    },
    {
      "type": "words",
      "start": "w:14-0.1",
      "items": [
        {
          "text": "Every small step",
          "at": "w:14"
        },
        {
          "text": "is a vote",
          "at": "w:20",
          "style": "accent"
        },
        {
          "text": "for who",
          "at": "w:23",
          "style": "small"
        },
        {
          "text": "you become",
          "at": "w:27",
          "style": "huge"
        },
        {
          "text": "Start before",
          "at": "w:31",
          "clear": true
        },
        {
          "text": "you are ready",
          "at": "w:33",
          "style": "strike",
          "strikeAt": "w:36"
        },
        {
          "text": "Start now.",
          "at": "w:36",
          "style": "huge"
        }
      ]
    }
  ],
  "music": {
    "mood": "cinematic",
    "drop": "w:14"
  }
}
```
