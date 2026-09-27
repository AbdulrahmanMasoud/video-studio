---
name: verdict
description: "Make a myth-busting / \"true or false\" / fact-check video: the claim appears and gets stamped MYTH with a buzzer, the real fact slides in with a check, reasons stack up, and a BUSTED or TRUE stamp lands at the end. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"verdict\", asks for a myth vs fact video, or describes this format."
---

# Verdict: myth vs fact

Dark charcoal with red and green glows; cream cards, MYTH/FACT tags, strike-through on the myth.

**Best for:** Correcting a misconception, fact-checking, "stop believing…".

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
   - Also for this template: The myth and the correct fact (verify facts; do not invent statistics).

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template verdict --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. `claim`: `mythAt` when the myth is stated, `stampAt` when the speaker says it's false, `factAt` when the truth is given.
2. `reason` lists the evidence (≤ 3 points).
3. Finish with `stamp` (BUSTED / TRUE / PARTLY TRUE).

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `claim` | `myth`, `fact`, `mythAt`, `stampAt`, `factAt` |
| `reason` | `title`, `points` [{`text`, `at`, `kind`: fact|myth, `icon`}] |
| `stamp` | `text`, `kind` myth|fact, `sub`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** `myth`, `fact`, `busted`.

## 5. Look and sound defaults

Captions `pill` · music `tension` ·
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
      "type": "claim",
      "start": 0,
      "myth": "You only use 10% of your brain",
      "mythAt": "w:0",
      "stampAt": "w:16",
      "fact": "Almost every region of your brain is active every day",
      "factAt": "w:17"
    },
    {
      "type": "reason",
      "start": "w:30-0.1",
      "title": "Why we know",
      "points": [
        {
          "text": "Scans show activity everywhere",
          "at": "w:30"
        },
        {
          "text": "Simple tasks light up large areas",
          "at": "w:33"
        },
        {
          "text": "Damage anywhere causes problems",
          "at": "w:38"
        }
      ]
    }
  ],
  "music": {
    "mood": "tension"
  }
}
```
