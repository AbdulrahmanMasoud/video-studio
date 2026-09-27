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
