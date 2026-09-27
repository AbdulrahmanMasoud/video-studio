---
name: whiteboard
description: "Make a whiteboard / sketch explainer video from a recording or script: hand-drawn titles, boxes and arrows that draw themselves, checklists, comparisons and circled key notes, synced to the voice. Use for concepts, processes, frameworks, \"how X works\". Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"whiteboard\", asks for a an explainer that draws itself video, or describes this format."
---

# Whiteboard: an explainer that draws itself

Off-white grid paper, marker strokes in ink and red, handwritten type, karaoke captions. Diagrams draw box by box as they are mentioned.

**Best for:** Explaining a concept, process, loop or framework; teaching.

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
$VT init JOB --template whiteboard --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace natural --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. Start with `title` (the question the video answers).
2. Use `diagram` for processes (2–5 nodes; `layout` vertical/horizontal/cycle; `circle` highlights the key node).
3. Use `list` for checklists, `compare` for two options, `note` for the final takeaway (it gets circled).

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `title` | `text`, `at`, `underlineAt` |
| `diagram` | `title`, `nodes` [{`text`, `at`, `color`: accent}], `layout` vertical|horizontal|cycle, `arrows` (false to hide), `circle` {`index`, `at`} |
| `list` | `title`, `items` [{`text`, `at`, `checkAt`, `check`: false}] |
| `compare` | `title`, `at`, `left` {`title`, `items` [{`text`, `at`} or strings]}, `right` {…} |
| `note` | `text`, `at`, `circleAt` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** none.

## 5. Look and sound defaults

Captions `karaoke` · music `acoustic` ·
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
      "text": "How startups grow",
      "at": 0.2,
      "underlineAt": "w:3"
    },
    {
      "type": "diagram",
      "start": "w:6-0.1",
      "title": "The loop",
      "nodes": [
        {
          "text": "Idea",
          "at": "w:10"
        },
        {
          "text": "Tiny version",
          "at": "w:15"
        },
        {
          "text": "Real users",
          "at": "w:20"
        }
      ],
      "circle": {
        "index": 2,
        "at": "w:26"
      }
    }
  ],
  "music": {
    "mood": "acoustic",
    "drop": "w:10"
  }
}
```
