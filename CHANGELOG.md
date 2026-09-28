# Changelog

All notable changes to this repository. Format: Keep a Changelog; versions are phases until the MVP ships.

## [Unreleased] — Phase 3: API, database, queues, compose stack

### API (`apps/api`, package `vs_api`)
- FastAPI app: auth (argon2, JWT access/refresh httpOnly cookies + CSRF double submit, bearer for API clients, email verification and
  password reset via Mailpit/Resend), `/me` + brand kit, `/templates` catalog (`packages/shared/templates.json` + `template_flags`),
  presigned direct-to-S3 uploads (POST policy enforces content type and size), projects (create → enqueue, list, get, delete, SSE events,
  texts, asset slots, render with credit reservation, retry, download), project assets (presign, register, list, patch, delete, limits),
  template requests, billing (plans, mock provider, checkout/portal stubs), admin (LLM routing in `app_settings`, grant credits, toggle
  templates, failed jobs, template requests), `/health` (db, redis, s3) and Prometheus-style `/metrics`.
- `vs_api.core`: SQLAlchemy 2 models (§5.7) + Alembic initial migration with seeded template flags; credit ledger with fast-path balance
  (reserve/commit/release/grant/renew, FOR UPDATE); state machine with `job_events`; RQ queues (`priority`, `transcribe`, `plan`, `render`,
  retry once, time-limited); S3 storage helpers; email; plans.yaml rules; LLM settings shared with the worker.
- Typed errors `{error_code, message}` on every 4xx/5xx; JSON request logs with `request_id`; slowapi per-IP limits on auth, Redis
  per-user limit on project creation; CORS locked to `WEB_ORIGIN`.

### Worker
- `vs_worker.tasks`: `preview_job`, `render_job`, `edit_job` (texts / asset slots) driving the Pipeline with status transitions, progress,
  credits, S3 downloads/uploads, emails; scratch job folder on the `jobs` volume with rebuild-from-plan fallback; `python -m vs_worker.rqworker`.
- Chromium launched with `--disable-dev-shm-usage --no-zygote`; `RENDER_WORKERS` (default 2) caps parallel pages in containers.

### Infra
- `docker-compose.yml` (postgres, redis, minio + bucket init, mailpit, api, worker), `infra/docker/api.Dockerfile`, `.env.example`,
  `Makefile` (`up`, `down`, `migrate`, `seed`, `test-api`, `test-api-integration`, `lint-api`), CI jobs for the API and the full flow.

## Phase 2 — 2026-09-28: LLM planner

### Worker (`apps/worker`)
- `vs_worker.llm.LLMClient`: one LiteLLM wrapper for Anthropic, OpenAI, Gemini, OpenRouter, Groq and Ollama; JSON mode where supported,
  fence stripping + balanced-object extraction + one repair pass otherwise; vision input (data URLs); fallback chain; per-request timeout;
  cost from LiteLLM's map or `packages/shared/plans.yaml` `llm_prices`.
- `vs_worker.llm.LLMSettings`: routing per task (`LLM_MODEL_PLANNER`, `LLM_MODEL_FAST`, `LLM_MODEL_VISION`, `PLANNER_MODEL_FREE/PAID`,
  `LLM_FALLBACK_CHAIN`, `PLANNER_VISION_REVIEW`), defaults follow the first provider with a credential, overridable from `app_settings` keys `llm.*`.
- `vs_worker.llm.MockLLM`: example plan re-anchored to the real transcript, media slots filled from the asset list, scripted responses for tests.
- `vs_worker.planner.LLMPlanner`: system prompt (role + template SKILL.md + plan schema + hard rules + asset rules), user message (brief,
  assets, shortened example (Arabic when applicable), indexed transcript); Pydantic + template-whitelist + anchor + asset-name validation,
  then `vt.py stills --auto` as the ground truth; ≤ 3 attempts then `plan_failed`; deterministic fallback when the LLM is unreachable;
  optional vision review of the contact sheet; `editable_fields` and `asset_slots`; usage/cost accounting on the job.
- Edit-decision step (fast model proposes `--drop` ranges; strict validation, drop nothing on doubt) and asset auto-description (vision).
- `Pipeline.apply_texts()` and `Pipeline.apply_assets()` (swap / remove / insert full-frame media at a word) → re-run stills.
- `python -m vs_worker.cli run|providers` for manual runs with a real provider.

### Engine
- `edit`: a word is kept only if its midpoint survives the cut (words whose start fell inside the 70 ms crossfade pad were kept before).

### Infra
- Dockerfile: the font cache layer now precedes pip, so dependency changes no longer re-download fonts.

## Phase 1 — 2026-09-27: engine productisation

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
