# Third-party software and licenses

Policy (brief §1): MIT / Apache-2.0 / OFL only for code and fonts that ship *in* the product. Tools invoked
as separate processes (ffmpeg, espeak-ng, Chromium) are listed with their licenses; see DECISIONS.md #9 for
how copyleft tooling is handled.

## Runtime (worker image)

| component | license | use | note |
|---|---|---|---|
| Python 3.12 | PSF | runtime | |
| numpy, scipy | BSD-3 | audio DSP (edit, SFX, music) | |
| soundfile (libsndfile) | BSD-3 (LGPL-2.1 lib) | WAV I/O | dynamically linked C library |
| Pillow | MIT-CMU | images, contact sheets | |
| pillow-heif | BSD-3 | HEIC/HEIF/AVIF decode | bundles libheif (LGPL-3), libde265 (LGPL-3); decode only, no x265 |
| playwright (Python) + Chromium headless shell | Apache-2.0 / BSD-3 | frame rendering | separate browser process |
| faster-whisper, CTranslate2 | MIT | transcription | Whisper weights: MIT (OpenAI) |
| pydantic | MIT | job specs | |
| ffmpeg (Debian bookworm build) | GPL-2.0+ (build enables GPL components: libx264) | decode/encode/mix | invoked as a subprocess, never linked |
| espeak-ng | GPL-3.0 | offline test voice (fixtures, `TTS_PROVIDER=espeak`) | subprocess; not used for customer output by default |
| tini | MIT | PID 1 signal forwarding | |
| fonts-noto-core (Debian) | OFL-1.1 | system fallback fonts | |
| Google Fonts families cached by `vt.py fonts --precache` | OFL-1.1 / Apache-2.0 (per family) | on-screen text | list in `engine/video-engine/scripts/vtlib/fonts.py` |

## Dev / test only

| component | license |
|---|---|
| pytest, pytest-timeout | MIT |
| ruff | MIT |
| mypy | MIT |
| uv | MIT / Apache-2.0 |

## Removed

| component | reason |
|---|---|
| edge-tts | unofficial Microsoft endpoint; not acceptable for a commercial product (replaced by `TTSProvider`, Phase 1) |

Later phases add: FastAPI, SQLAlchemy, Alembic, RQ, redis-py, boto3, LiteLLM, argon2-cffi, Next.js and their
dependencies; keep this table updated when `requirements.txt` / `package.json` change.
