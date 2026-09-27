# Intake

Ask only what is missing. Never start producing before **language** and **dimensions** are known.

## Required (always ask if not given)

| Question | Why it matters | Accepted answers |
|---|---|---|
| What language is the video in? | transcription model, fonts, text direction, captions, numerals, TTS voice | any language name or ISO code (`en`, `ar`, `ar-EG`, `es`, `hi`, `ja`, `zh`…) |
| What size / aspect ratio? | layout, safe zones, render resolution | `9:16`, `1:1`, `4:5`, `16:9`, `2:3`, `3:4`, `21:9`, `4k-9:16`, `4k-16:9`, `720p-9:16`, `720p-16:9`, aliases `tiktok`, `reels`, `shorts`, `story`, `feed`, `square`, `youtube`, or exact `WIDTHxHEIGHT` |

Suggested wording (adapt to the user's language):

> Before I start: **which language** is the video in, and **what size** do you need?
> 9:16 (TikTok/Reels/Shorts) · 1:1 (square) · 4:5 (Instagram) · 16:9 (YouTube) · or a custom size.

If the user wants several sizes, produce one job per size (the same plan usually works; check
the stills for each).

## Also establish (ask briefly, or assume and say so)

| Topic | Default if not specified |
|---|---|
| Source: recording / camera video / script (AI voice) / no voice | whatever the user uploaded; if only text, offer AI voice or text-only |
| Platform | `tiktok` for 9:16, `youtube` for 16:9, `none` otherwise |
| Target length | as short as the content allows; ≤ 60 s for vertical social |
| Brand colors / fonts | template palette; Google Fonts picked for the language |
| Music | template's mood; `none` for podcasts; user track if provided |
| Caption style | template default; `none` if the user asks for no captions |
| Numerals (Arabic, Persian…) | `auto` (locale default); `latin` or `native` on request |

## Size presets

| Preset | Pixels |
|---|---|
| 9:16 / vertical / tiktok / reels / shorts / story | 1080×1920 |
| 4:5 / feed | 1080×1350 |
| 1:1 / square | 1080×1080 |
| 16:9 / landscape / youtube | 1920×1080 |
| 2:3 · 3:4 · 21:9 | 1080×1620 · 1080×1440 · 2520×1080 |
| 4k-9:16 · 4k-16:9 | 2160×3840 · 3840×2160 |
| 720p-9:16 · 720p-16:9 | 720×1280 · 1280×720 |

Any other ratio (`a:b`) is scaled so the short side is 1080 px. `WxH` is used as-is (rounded to even).
