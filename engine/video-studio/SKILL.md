---
name: video-studio
description: "Start here for any request to make, edit or produce a video: reels, TikToks, YouTube Shorts, explainers, ads, tutorials, podcasts clips, talking-head edits. Picks the best of 24 Video Studio templates for the content, runs the intake (language and dimensions are always asked if missing), then produces a professional MP4 with the video-engine. Use when the user wants a video but has not named a template, asks which style fits, or says \"video studio\"."
---

# Video Studio

Video Studio produces finished, professionally edited videos from a voice note, a camera video, a
screen recording or just a script, in **any language** and **any size**. It has 24 templates
(each is its own skill) plus a shared engine (`video-engine`).

## 1. Intake: ask first, in one message

If any of these are unknown, ask before doing anything else (use a question/options tool if the
environment has one):

1. **Language** of the video.
2. **Dimensions**: 9:16 (TikTok/Reels/Shorts) · 1:1 · 4:5 · 16:9 (YouTube) · custom WxH.
3. **What you have**: voice recording, camera video, screen recording, photos, or only a script/idea.

Assume and state the rest (platform from the size, template default music, target length).
If the user has only an idea, write a tight script for them first (hook in the first sentence,
one idea per sentence, 30–60 s), get a quick OK, then voice it (`vt.py tts`) or ask them to record it.

## 2. Pick the template

| template | category | best for | scenes |
|---|---|---|---|
| `steps` | Education | Any content with a clear sequence of tips, steps or rules. | `hook`, `count`, `step`, `outro` |
| `whiteboard` | Education | Explaining a concept, process, loop or framework; teaching. | `title`, `diagram`, `list`, `compare`, `note` |
| `quiz` | Engagement | Trivia, test-your-knowledge, "can you guess", educational checks. | `question`, `explain`, `score` |
| `before-after` | Marketing | Anything with a clear before state and after state. | `compare`, `split` |
| `mirror` | Talking head | The user recorded themselves talking to camera. | `talk`, `title`, `lower` |
| `podcast` | Talking head | Two or three people talking; interview or podcast highlights. | `split`, `solo`, `quote` |
| `storytime` | Talking head | Narrative content: "the day I…", journeys, lessons, confessions. | `chapter`, `talk`, `photo`, `end` |
| `verdict` | Education | Correcting a misconception, fact-checking, "stop believing…". | `claim`, `reason`, `stamp` |
| `hot-take` | Opinion | Opinions, debates, "unpopular opinion", engagement bait done tastefully. | `take`, `poll`, `cta` |
| `chat` | Tech | Demonstrating prompts, AI answers, chatbot flows, DMs. | `chat`, `result` |
| `terminal` | Tech | CLI tools, install guides, git, npm, Python, DevOps, error fixes. | `terminal`, `callout` |
| `screen` | Tech | Product demos, feature tours, onboarding, how-to-use-this-app. | `demo`, `step` |
| `showcase` | Marketing | E-commerce, launches, merch, apps, services. | `product`, `cta` |
| `counter` | Data | Any script built around numbers. | `stat`, `compare` |
| `top-five` | Entertainment | Rankings, best-of lists, favorites, countdowns. | `intro`, `rank` |
| `flash-sale` | Marketing | Discounts, Black Friday, launches with deadlines. | `sale`, `items`, `cta` |
| `echo` | Typography | Motivation, quotes, manifesto-style statements, voice-only content. | `flow`, `words`, `quote` |
| `cinema` | Storytelling | Storytelling with footage/photos, brand films, trailers, travel films. | `title`, `shot`, `chapter`, `end` |
| `journey` | Storytelling | Histories, career stories, product evolution, roadmaps. | `timeline`, `milestone` |
| `breaking` | News | News, updates, announcements, launches, recaps. | `headline`, `point` |
| `city-map` | Travel | Travel guides, food tours, day plans, store locations. | `map`, `place` |
| `recipe` | Food | Recipes, drinks, meal prep, baking. | `title`, `ingredients`, `step`, `final` |
| `workout` | Fitness | Home workouts, gym routines, stretching, challenges. | `exercise`, `rest`, `done` |
| `review` | Reviews | Reviews, comparisons, "is it worth it". | `score`, `pros`, `cons`, `verdict` |

Quick guide:
- Talking to camera → `mirror` (tips, opinions) or `storytime` (stories); two people → `podcast`.
- Teaching → `steps` (sequences), `whiteboard` (concepts), `quiz` (test), `verdict` (misconceptions).
- Tech → `chat` (AI prompts), `terminal` (CLI), `screen` (apps/websites).
- Selling → `showcase` (product), `flash-sale` (discount), `before-after` (results), `review`.
- Data and lists → `counter` (numbers), `top-five` (rankings), `journey` (timelines), `breaking` (news).
- Mood pieces → `echo` (kinetic type for voice-only), `cinema` (footage with a film look).
- Lifestyle → `recipe`, `workout`, `city-map` (travel).

If two fit, pick one and say why in one sentence; offer the other as an alternative. The user can
always name a template directly ("use the quiz skill").

## 3. Produce

Open the chosen template's `SKILL.md` (sibling folder, e.g. `../quiz/SKILL.md`) and follow it. It
uses the engine at `../video-engine/scripts/vt.py`; the full pipeline, standards and references are
in `../video-engine/SKILL.md`. List installed templates any time with:

```bash
python3 ${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py templates
```

## 4. Deliver

Deliver `final.mp4` with one line: template, language, size, duration. Offer one concrete next step
(another size, another language, a shorter cut).
