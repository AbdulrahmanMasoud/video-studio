---
name: terminal
description: "Create a coding / command-line / developer tutorial video: a terminal window where commands type themselves, output prints in color (success, errors, warnings, highlights), the camera zooms into key lines, and callout cards explain the fix. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"terminal\", asks for a developer / CLI demos video, or describes this format."
---

# Terminal: developer / CLI demos

Deep navy with a subtle moving grid, macOS-style terminal, green prompt, monospace font, boxed captions.

**Best for:** CLI tools, install guides, git, npm, Python, DevOps, error fixes.

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
   - Also for this template: The exact commands and outputs to show.

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template terminal --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. One `terminal` scene per session; `cmd` lines type between `at` and `end`; outputs appear at `at`.
2. Use `zoomAt`/`zoomEnd` on the line the voice explains.
3. Use `callout` for the key takeaway or fix.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `terminal` | `title`, `prompt` ("$ "), `fontSize` (U), `lines` [{`text`, `kind`: cmd|out|ok|err|warn|hl|comment, `at`, `end`}], `zoomAt`, `zoomEnd`, `zoom` |
| `callout` | `title`, `text`, `sub`, `kind` ok|err|warn|info, `icon`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** none.

## 5. Look and sound defaults

Captions `boxed` · music `ambient` ·
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
      "type": "terminal",
      "start": 0,
      "title": "~/projects — zsh",
      "lines": [
        {
          "text": "npx create-app my-site",
          "kind": "cmd",
          "at": "w:9",
          "end": "we:12"
        },
        {
          "text": "? Project name › my-site",
          "kind": "out",
          "at": "w:13"
        },
        {
          "text": "Installing dependencies…",
          "kind": "out",
          "at": "w:18"
        },
        {
          "text": "added 312 packages in 3s",
          "kind": "ok",
          "at": "w:20"
        },
        {
          "text": "npm run dev",
          "kind": "cmd",
          "at": "w:25",
          "end": "we:28"
        },
        {
          "text": "ready - local: http://localhost:3000",
          "kind": "hl",
          "at": "w:31"
        },
        {
          "text": "Error: port 3000 already in use",
          "kind": "err",
          "at": "w:34"
        }
      ],
      "zoomAt": "w:31",
      "zoomEnd": "w:34"
    },
    {
      "type": "callout",
      "start": "w:42-0.1",
      "kind": "ok",
      "title": "Change the port",
      "text": "npm run dev -- --port 3001",
      "at": "w:42"
    }
  ],
  "music": {
    "mood": "ambient"
  }
}
```
