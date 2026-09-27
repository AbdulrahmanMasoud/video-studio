---
name: steps
description: "Turn a voice note, video or script into a polished numbered-tips video (\"3 ways to…\", \"4 steps to…\", how-to, tutorial, prompt tips) with a step tracker, typed prompt cards with bad→good rewrites, lists and A/B toggles. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"steps\", asks for a numbered tips with a progress tracker video, or describes this format."
---

# Steps: numbered tips with a progress tracker

Bold cobalt background, a pill tracker that fills as each step is covered, a big number count-in, and one visual card per step: a typed prompt (with an "unclear" stamp on the bad version and highlights on the good one), a list, A/B toggles or a statement card.

**Best for:** Any content with a clear sequence of tips, steps or rules.

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
   - Also for this template: How many steps/tips the video covers (usually obvious from the script).

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template steps --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. Open with `hook` (the promise/title, ≤ 6 words) for the first sentence.
2. Use `count` when the speaker announces the number of tips; anchor `at` on the number word.
3. One `step` per tip. `short` is 1 word for the tracker. Pick the card kind that shows the tip: `prompt` for before/after wording, `list` for questions/ingredients, `toggles` for choices, `text` for a one-liner.
4. Close with `outro` (the takeaway; `strikeAt` crosses out a misconception like "magic").

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `hook` | `title`, `icon` (robot, bulb, question, star, none), `at`, `beats` [{`at`, `kind`: sparkle|confused}] |
| `count` | `n`, `at` (number slam), `text`, `textAt` |
| `step` | `n` (auto), `short` (tracker label), `title`, `card`: `{kind:'prompt', label, bad:{text,at,end,stamp}, good:{text,at,end}, highlights:[{text,at}]}` · `{kind:'list', items:[{text,at,icon}]}` · `{kind:'toggles', items:[{a,b,at,flipAt}]}` · `{kind:'text', text, at}` |
| `outro` | `kicker`, `strikeAt`, `label`, `text`, `highlight`, `textAt`, `cta` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** `prompt`, `unclear`.

## 5. Look and sound defaults

Captions `pill` · music `lofi` ·
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
      "type": "hook",
      "start": 0,
      "title": "How to write a great prompt",
      "icon": "robot",
      "beats": [
        {
          "at": "w:3",
          "kind": "sparkle"
        },
        {
          "at": "w:7",
          "kind": "confused"
        }
      ]
    },
    {
      "type": "count",
      "start": "w:18-0.1",
      "n": 4,
      "at": "w:21",
      "text": "things that change everything",
      "textAt": "w:22"
    }
  ],
  "music": {
    "mood": "lofi",
    "drop": "w:21"
  }
}
```
