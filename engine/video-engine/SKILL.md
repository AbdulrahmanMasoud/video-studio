---
name: video-engine
description: Shared rendering engine for the Video Studio template skills (steps, quiz, chat, mirror, podcast, top-five and 18 more). Turns a voice recording, a camera video or a written script into a finished, professionally edited MP4 in any language and any size, with auto-trimmed voice, animated scenes, synced captions, sound effects, music and loudness mastering. Use it whenever a Video Studio template skill tells you to, or when the user asks for a produced/edited short video, reel, TikTok, Short or explainer from their audio, footage or script and no template has been picked yet.
---

# Video Engine

This folder is the production pipeline that every Video Studio template uses. A **template skill**
(for example `steps`, `quiz` or `mirror`) decides the look and the storyboard. This skill does the
actual work: transcription, cleanup edit, animation rendering, sound design, mixing and QA.

Every command below is run with the CLI at `scripts/vt.py` inside this folder. Resolve its path
before starting:

- Claude Code plugin: `${CLAUDE_SKILL_DIR}/scripts/vt.py` (from this skill), or
  `${CLAUDE_SKILL_DIR}/../video-engine/scripts/vt.py` (from a template skill).
- Any other install: the `video-engine` folder is a sibling of the template skill folders;
  use `<template skill folder>/../video-engine/scripts/vt.py`.

Below, `VT` means `python3 <that path>`.

## 0. Intake: never skip this

A video cannot be produced correctly without two answers. **If the user has not already given them,
ask before doing anything else**:

1. **Language** of the video (the spoken language and the on-screen text language). Examples:
   English, Egyptian Arabic, Spanish, Hindi, Japanese. Do not assume it from the user's chat
   language when they upload media; confirm.
2. **Dimensions**: aspect ratio or pixel size. Offer the common choices: `9:16` (TikTok, Reels,
   Shorts), `1:1` (feed), `4:5` (Instagram portrait), `16:9` (YouTube), or custom `WIDTHxHEIGHT`.

Ask these together, as one short message (or one call to an options/question tool if available).
Then ask, or infer sensibly and state your assumption, for the rest of the brief:

3. **Source**: voice recording, camera video (talking head), a script to voice with AI TTS, or
   no voice (music + on-screen text only).
4. **Platform** (sets safe zones so captions avoid UI overlays): `tiktok`, `reels`, `shorts`,
   `youtube`, `linkedin`, `x`, `none`.
5. Target length, brand colors/fonts, music preference (mood, own track, or none), caption style.

`vt.py init` refuses to run without `--lang` and `--size`. That is deliberate: if you hit that
error, go back and ask the user. Full question bank and defaults: `references/intake.md`.

## 1. Environment (once per machine)

```bash
VT doctor            # checks ffmpeg, Python modules, headless Chromium
VT setup             # installs Python deps + Chromium (add --break-system-packages on managed Pythons)
```

ffmpeg must be installed by the OS package manager if `doctor` reports it missing.

## 2. Create the job

```bash
VT init ./jobs/my-video --template steps --lang ar --size 9:16 --platform tiktok --input /path/voice.m4a
```

Options: `--fps 30|60`, `--lufs -14` (loudness target), `--numerals auto|latin|native`,
`--captions pill|karaoke|pop|line|boxed|none`, `--palette '{"bg":"#101820","accent":"#FEE715"}'`,
`--fonts '{"display":"Cairo"}'`, `--dir rtl|ltr` (override). A camera video as `--input` works too:
its audio becomes the voice and the footage is cut with the same edit.

## 3. Get words with timestamps

- Recording or video: `VT transcribe JOB` (faster-whisper, word-level). `--model small` is faster,
  `medium` (default) is better for Arabic and other non-English speech. `--prompt "names, jargon"`
  improves spelling.
- Script only: write it to a text file, then `VT tts JOB --text-file script.txt [--voice NAME] [--provider openai]`
  (needs `TTS_PROVIDER=openai` + `OPENAI_API_KEY`; `--provider espeak` is an offline test voice). TTS writes
  `tts.mp3` and makes it the job input; run `VT transcribe JOB` afterwards for the word timings.
- No voice at all: skip this step and give the plan a `"duration"` in seconds.

Read `transcript.txt`. Each line is `[index] word@seconds`. Low-confidence words are marked `?`.

## 4. Clean edit (voice)

```bash
VT analyze JOB       # speech map, long pauses, clipping, retake/stumble candidates -> analysis.txt
VT edit JOB --pace tight --drop "w:40-w:43,31.2-32.0" --sections "12,57"
```

- Read `analysis.txt` and the transcript. Remove false starts, repeated takes and stumbles with
  `--drop` (word ranges `w:A-w:B` inclusive, or seconds). When a phrase was said twice, keep the
  better (usually the last) take.
- `--pace tight` trims pauses for social video; `natural` for storytelling; `relaxed` for calm
  content; `none` keeps timing.
- `--sections` lists word indices that start a new beat; they get a slightly longer breath.
- The edit also cleans the voice (de-clip, EQ, de-ess, compression, loudness) and, for a camera
  input, cuts the footage identically into `cam_edit.mp4`.
- Output: `words_edit.json` + `transcript_edit.txt`. **All plan anchors must use the indices in
  `transcript_edit.txt`**, not the original transcript.

Camera footage or images used by a template are registered with `VT media JOB --name cam`
(defaults to `cam_edit.mp4`), `--name screen --video rec.mp4`, `--name photo --image pic.jpg`.
Images may be JPG, PNG (alpha kept: use `--fit contain` for cut-outs), WebP or HEIC (converted, EXIF
rotation applied and metadata stripped). Clips accept `--start S --duration D` (trim) and lose their audio
unless `--keep-audio` is given (then it is mixed in at the scene that shows the clip). Many assets at once:
`VT assets JOB --manifest assets.json` (list of `{name, path, description?, fit?, start?, duration?, keep_audio?}`),
which also writes `media/index.json` (name, kind, size, duration, alpha).

## 5. Storyboard: write `JOB/plan.json`

This is where the craft is. Follow the template skill's storyboard rules and scene schema. General
rules (full schema in `references/plan-schema.md`):

- `scenes` is an ordered list; each has a `type` from the template, a `start`, and fields.
  A scene ends where the next one starts.
- Time values accept seconds or word anchors: `"w:12"` (start of word 12), `"we:12"` (end of
  word 12), `"w:12+0.3"`, `"w:12-0.1"`. Anchor every reveal to the word that says it, so visuals
  land exactly on the voice. Start a scene ~0.1 s before its first word (`"w:26-0.1"`).
- **All on-screen text must be in the video language**, including labels the template would
  otherwise print in English: set `"labels": {...}` (keys listed in each template's SKILL.md), and
  write every title, option and card in that language. Keep on-screen text short: it
  summarizes the voice, it does not transcribe it (captions already do).
- Set `"lang"` in the plan. RTL languages (Arabic, Persian, Urdu, Hebrew…) mirror automatically.
- Optional: `"music": {"mood": "lofi", "drop": "w:21", "end": "w:90", "stops": ["w:40~w:42"]}`,
  `"captions": {...}`, `"palette": {...}`, `"sfx": [{"t": "w:30", "sfx": "ding"}]`,
  `"mix": {"music_db": -13}`, `"data": {...}` (template-level data such as a ticker).

## 6. Preview before rendering

```bash
VT stills JOB --auto            # one frame per scene + qa/contact_sheet.jpg
VT stills JOB --times 1.2,4,7.5 # specific moments
```

**Look at `qa/contact_sheet.jpg`.** Check: text fits and is readable, nothing hides under captions
or platform UI, the right script/direction is used, reveals happen on the right words, no empty
frames. Fix the plan and re-run stills until it is right. This costs seconds; a full render
costs minutes.

## 7. Build

```bash
VT build JOB                    # render + sfx + music + mix + mux + qa  ->  JOB/final.mp4
VT build JOB --draft            # half resolution, for a fast full check
VT build JOB --no-music
```

Single steps exist for iteration: `render`, `sfx`, `music` (`--mood`, `--file song.mp3`, `--none`),
`mix` (`--music-db`, `--sfx-db`, `--no-duck`), `mux`, `qa`.

`mux` (and `build`) also take `--watermark logo.png [--watermark-pos br|bl|tr|tl|center] [--watermark-opacity 0.6]`
and `--max-height 720` (caps the short side, i.e. 720p for both portrait and landscape). QA compares against
the delivered size, so drafts and capped deliveries are not flagged as wrong resolution.

Machine use: `VT --json <cmd>` (or `VT_JSON=1`) prints one JSON object per log line (`level`, `msg`, `progress`,
`error_code`), `VT_OFFLINE=1` makes any network call fail fast (fonts must be pre-cached: `VT fonts --precache`),
`init --duration-limit 600` refuses long inputs, and the CLI stops its ffmpeg/Chromium children on SIGTERM.

## 8. QA and delivery

Open `qa/report.json` and look at `qa/final_sheet.jpg` (10 frames across the video). Confirm:
resolution and fps as requested, integrated loudness about -14 LUFS (or the target), true peak
≤ -1 dBTP, no black gaps, captions in sync. Then give the user `final.mp4` (copy it wherever the
environment expects deliverables) with a two-line summary: length, size, language, template.

## Production standards

The bar is "a professional editor made this". `references/production-standards.md` covers
hook timing, pacing, caption rules, motion, sound design and mix levels. The most important:

- First visual change within 0.3 s; the hook must be readable in the first 2 s.
- Something moves or changes at least every ~1.5 s; no static holds over 3 s.
- Every reveal has a sound; sounds are subtle (the voice always wins).
- Captions: short chunks, highlighted active word, never covering key visuals.

## References

- `references/intake.md`: questions, defaults, size presets
- `references/plan-schema.md`: the plan format shared by all templates
- `references/production-standards.md`: editing, motion and audio rules
- `references/sfx-library.md`: sound effect names; `references/music-moods.md`: music moods
- `references/languages.md`: fonts, RTL, numerals, TTS voices
- `references/template-authoring.md`: how to build a new template
- `references/troubleshooting.md`: common errors and fixes
