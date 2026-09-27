# Changelog

All notable changes to this repository. Format: Keep a Changelog; versions are phases until the MVP ships.

## [Unreleased] — Phase 1: engine productisation

### Engine (`engine/video-engine`)
- `vt.py --json` / `VT_JSON=1`: one JSON object per log line (`level`, `msg`, `progress`, `error_code`).
- `VT_OFFLINE=1`: any non-loopback network call fails fast (socket guard); fonts fall back to the cache/system.
- `vt.py fonts --precache`: caches every Google Fonts family for all scripts and roles (image build step).
- `vt.py init --duration-limit S` (error `input_too_long`), non-media inputs rejected (`input_invalid`),
  `intake_missing` error code; `input_duration` recorded in `job.json`.
- `vt.py mux/build --watermark PNG --watermark-pos --watermark-opacity --watermark-scale` and `--max-height`
  (short-side cap); QA compares against the delivered size (`output_size`) and explains drafts/caps in `note`.
- `vt.py tts`: edge-tts removed; `TTSProvider` interface with `openai` and `espeak` providers, off by default.
  TTS now only produces `tts.mp3`; timings come from `transcribe`.
- `vt.py media`: HEIC/HEIF/AVIF/WebP conversion (pillow-heif), EXIF rotation applied and metadata stripped,
  alpha kept as PNG, 40 MP guard, 4096 px cap; clips: `--start/--duration/--max-duration`, audio dropped unless
  `--keep-audio` (then mixed in at the scene). `vt.py assets JOB --manifest` registers many and writes `media/index.json`.
- SIGTERM/SIGINT stop child processes and exit 143/130; `run()` gained a timeout.
- Structured `progress` events from the renderer; browser errors are `warning` events.

### Worker (`apps/worker`)
- `vs_worker.pipeline.Pipeline`: `prepare_preview()` → `apply_plan()` → `render()` with step events, timeouts,
  typed errors (`PipelineError` with `code`, `transient`, `user_error`).
- `vs_worker.engine.EngineRunner`: subprocess driver for the CLI (JSON events, timeouts, process-group kill).
- Deterministic fallback planner for `steps`, `mirror` and a `text`-scene generic for every other template.
- Offline fixtures (espeak-ng voice, testsrc2 footage, HEIC, transparent PNG, 90 s clip) and pytest suite.

### Infra
- `infra/docker/worker.Dockerfile`: pinned deps (`uv pip compile`), whisper model baked, fonts pre-cached,
  espeak-ng, tini, non-root. `Makefile` targets, GitHub Actions `ci.yml`.

## Phase 0 — 2026-09-27
- Imported the engine (24 templates + `video-engine`) and dev tools; verified inside Docker; architecture docs.
