---
name: chat
description: "Show an AI chat conversation as a video: a chat window where the user's messages send, the AI shows typing dots then streams its reply, with reactions and auto-scroll, plus a result card. Great for prompt demos, \"I asked ChatGPT/Claude…\" and AI tips. Works in any language (RTL included) and any size (9:16, 1:1, 4:5, 16:9, custom); asks for the language and dimensions if they were not given. Use when the user says \"chat\", asks for a AI conversations video, or describes this format."
---

# AI Chat: AI conversations

Dark gradient with soft color blobs, a light chat window, indigo user bubbles, white AI bubbles, typing status in the header.

**Best for:** Demonstrating prompts, AI answers, chatbot flows, DMs.

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
   - Also for this template: The exact messages to show (user and AI).

## 2. Produce

```bash
VT="python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py"   # or <this skill folder>/../video-engine/scripts/vt.py
$VT doctor                                   # first time: $VT setup
$VT init JOB --template chat --lang <LANG> --size <SIZE> --platform <PLATFORM> --input <VOICE_OR_VIDEO>
$VT transcribe JOB          # or: $VT tts JOB --text-file script.txt   (no recording)
$VT analyze JOB
$VT edit JOB --pace tight --drop "<stumbles, e.g. w:12-w:15>"
# write JOB/plan.json (storyboard below), anchoring times to transcript_edit.txt
$VT stills JOB --auto       # inspect JOB/qa/contact_sheet.jpg and fix the plan
$VT build JOB               # -> JOB/final.mp4, then check JOB/qa/final_sheet.jpg and qa/report.json
```

## 3. Storyboard rules

1. One `chat` scene holds the whole exchange; anchor each message's `at`/`end` to when the voice says it.
2. Keep AI replies short (≤ 5 lines); use `\n•` for bullet lines.
3. End with `result` summarizing the takeaway.

General rules (all templates): anchor every reveal to the word that says it (`"w:12"`, `"we:12"`,
`"w:12-0.1"`); start scenes ~0.1 s before their first word; keep on-screen text short and **in the
video language**; translate template labels with `"labels"`; one idea per scene; hold the last
scene ≥ 1.2 s after the final word. Plan format: `video-engine/references/plan-schema.md`.

## 4. Scenes

| type | fields |
|---|---|
| `chat` | `title`, `messages` [{`from`: user|ai, `text`, `at`, `end`, `think` (typing-dots seconds), `react`: heart|star|fire|check}] |
| `result` | `title`, `text`, `icon`, `at` |
| `text` | common: `text`, `sub`, `at` (a big statement card) |
| `media` | common: `media`, `text`, `kenburns` (full-frame b-roll) |

All times accept seconds or word anchors. Optional on every scene: `transition`
(`slide`, `fade`, `zoom`, `push`, `cut`) and `end`.

**Translatable labels:** `assistant`, `typing`, `online`.

## 5. Look and sound defaults

Captions `line` · music `lofi` ·
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
      "type": "chat",
      "start": 0,
      "title": "AI Assistant",
      "messages": [
        {
          "from": "user",
          "text": "Plan my week. I have a job, the gym 3x, and a side project.",
          "at": "w:13",
          "end": "we:27"
        },
        {
          "from": "ai",
          "text": "Happy to! One question first: when do you have the most energy?",
          "at": "w:28",
          "end": "we:39",
          "think": 0.6
        },
        {
          "from": "user",
          "text": "Mornings",
          "at": "w:40",
          "end": "we:42",
          "react": "heart"
        },
        {
          "from": "ai",
          "text": "Here's your week:\n• 7–9am deep work on the side project\n• 9–5 job\n• Mon/Wed/Fri gym after work\n• Sunday: review & plan",
          "at": "w:43",
          "end": "we:60"
        }
      ]
    },
    {
      "type": "result",
      "start": "w:61-0.1",
      "title": "Try it yourself",
      "text": "Tell it your constraints, let it ask questions, then ask for the schedule.",
      "at": "w:61"
    }
  ],
  "music": {
    "mood": "lofi"
  }
}
```
