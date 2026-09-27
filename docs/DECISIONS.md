# Decisions

Format: date, decision, why. Newest at the bottom. The brief (`VIDEO_STUDIO_SAAS_BRIEF.md`) is the
source of requirements; this file records the defaults we picked where the brief left room.

## 2026-09-27 — Phase 0

1. **Monorepo root is this repository** (`video-studoi/`), not a nested `video-saas/` folder. The
   brief's layout is applied at the repo root. Why: the owner already initialised git here; nesting
   would add a pointless level.
2. **`engine/` is `plugins/video-studio/skills` verbatim**, plus the upstream `LICENSE` copied in as
   `engine/LICENSE`. The empty stray directory `video-engine/{scripts` from the zip was dropped.
   `docs/previews/*.jpg` from the zip were kept (used by the landing page gallery).
3. **`engine-dev/` path fix**: `SK = ROOT / "engine"` and smoke output in `engine-dev/_smoke/`
   (git-ignored). The `examples/*.py` helpers import `mkplan` relatively and needed no change.
4. **Whisper model in the image is a build arg** (`WHISPER_MODEL`, default `small`). Prod builds pass
   `medium`. Why: the brief wants `small` in tests and `medium` in prod from one Dockerfile.
5. **Worker base image**: `python:3.12-slim-bookworm` + Debian ffmpeg + Playwright's own Chromium
   (`playwright install --with-deps chromium`). Why: the Playwright pip version pins the browser build,
   avoiding a mismatch with a distro Chromium.
6. **`espeak-ng` and `tini` are installed in the worker image** already in Phase 0. espeak-ng is the
   offline speech source for test fixtures (Phase 1); tini gives clean SIGTERM handling for the CLI.
7. **Non-root worker** (`uid 10001`), caches under `/cache` (`VT_CACHE`, `HF_HOME`), jobs under `/jobs`.

## 2026-09-27 — Phase 1

8. **`--max-height` caps the short side**, not literally the height: `720` gives 1280×720 for landscape and
   720×1280 for portrait. Why: the plans speak of "720p" for the free tier and a portrait video with a 720 px
   height would be unusably small. Documented in the CLI help and SKILL.md.
9. **Copyleft tooling policy.** ffmpeg (Debian build, GPL) and espeak-ng (GPL) run as separate processes and
   are never linked into our code; pillow-heif bundles LGPL decoders. The brief's "MIT/Apache/OFL only" is
   applied to code and fonts shipped in the product; process-level tools are recorded in `docs/THIRD_PARTY.md`.
   Flagged to the owner as a question (HEVC/HEIC decoding also has patent implications for a commercial service).
10. **TTS timings come from transcription**, never from the provider. The espeak provider exists only for
    offline tests and fixtures; the default is `TTS_PROVIDER=none` so the product cannot accidentally use it.
11. **Clip audio (`--keep-audio`)** is stored as `media/<name>.wav` and mixed in by `vt.py mix` at the start of the
    scene whose `media` field names the clip, at −6 dB, trimmed to the scene length. The engine's frame-sequence
    media has no audio otherwise.
12. **Fallback planner covers all templates**: dedicated storyboards for `steps` and `mirror` (as required) and
    the common `text` scene per section for the other 22, so a job can always reach `preview_ready`.
13. **The pipeline never skips a step on re-run**; the engine overwrites its outputs deterministically, which is
    what makes retries safe. Idempotency is tested by rendering twice into the same folder.
14. **Font pre-cache is its own Docker layer** built from only `fonts.py` + `common.py`, so ordinary engine edits
    do not trigger the slow network-bound download again.
15. **Asset validation lives in two places**: real-content and size checks in the engine (`media`/`assets`, error
    `asset_invalid`), asset-*name* validation in the planner (Phase 2) because `engine.js` draws a placeholder for
    unknown media instead of failing.
16. **`VS_ENGINE_DIR` / `VS_REPO_ROOT`** env vars let the worker find the engine outside the repo layout (Docker).
17. **Mix true-peak ceiling lowered from −1.2 to −1.5 dBTP.** The AAC encoder in `mux` overshoots by about
    0.3 dB, so the delivered file measured −0.9 dBTP against the documented “≤ −1 dBTP” standard. With −1.5 the
    final lands around −1.2. The QA threshold itself (−0.5) is unchanged.
