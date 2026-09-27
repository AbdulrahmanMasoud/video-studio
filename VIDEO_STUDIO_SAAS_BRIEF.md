# Video Studio SaaS: engineering brief for Claude Code

You are the lead software engineer and AI engineer on this project. Read this whole document before
writing any code. Then work through the phases in order, testing everything you build. Do not skip
tests, do not fake test results, and do not mark a phase done until its "Definition of done" passes
on a clean `docker compose up`.

Date: 2026-09-27. Owner: the person talking to you (a content creator building a micro-SaaS).
Language of all code, comments, docs and commit messages: English. The product UI is bilingual
(English + Arabic, RTL).

---

## 0. What we are building

**Product:** a web app where a user uploads a voice note, a talking-head video or a script, picks a
template, language and size, and receives a finished, professionally edited short video (animated
scenes synced to every spoken word, captions, sound effects, music, mastered audio). Any language,
any aspect ratio. Free tier with watermark, paid plans with credits.

**The rendering engine already exists.** The owner will give you a folder (from
`video-studio.zip`) containing a Claude plugin with 24 template skills and a shared engine. The
engine is a working CLI (`vt.py`) that does transcription, clean editing, rendering (headless
Chromium), sound effects, music, mixing and QA. Your job is to wrap it in a production SaaS:
API, job queue, workers, LLM storyboarding, web app, billing, Docker.

Study the engine first (Phase 0). Do not rewrite it. Fix it where needed, keep its CLI contract.

---

## 1. Non-negotiable decisions

| Topic | Decision |
|---|---|
| Runtime | Everything runs with Docker and `docker compose` (dev and prod). One `docker compose up` must bring up the whole stack locally. |
| Database | PostgreSQL 16 directly (no Supabase, no ORM magic beyond SQLAlchemy 2 + Alembic migrations). |
| Queue | Redis 7 + RQ (Python). Jobs are idempotent, retried once, and time-limited. |
| API | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2 (async), Alembic, `uv` or `pip-tools` for pinned deps. |
| Worker | Python 3.12 image with ffmpeg, Playwright Chromium, faster-whisper (model baked in at build), fonts pre-cached. Runs the engine CLI. |
| Web | Next.js 15 (App Router), TypeScript, Tailwind, `next-intl` for en/ar with RTL. |
| Object storage | S3-compatible: MinIO in dev, Cloudflare R2 (or any S3) in prod. Same code path (boto3, presigned URLs). |
| LLM | Provider-agnostic through LiteLLM. Must work with **all** of: Anthropic (default), OpenAI, Google Gemini, OpenRouter (any model behind it), Groq, and Ollama (local). The model per task is a runtime setting (DB-backed, editable via admin endpoint, no redeploy), with env defaults. Every provider is exercised by the same test-suite through the mock; a real-provider smoke test runs for each provider whose API key is present. |
| Transcription | faster-whisper in the worker (default `medium`, `small` in tests). Optional cloud transcription provider interface, not required for MVP. |
| TTS | **Remove `edge-tts`** (unofficial endpoint, not acceptable for a commercial product). Replace with a `TTSProvider` interface with an OpenAI TTS implementation (behind a feature flag, off by default). Word timings for TTS audio come from transcribing the generated audio. |
| Payments | Lemon Squeezy (merchant of record) via hosted checkout + webhooks. A `mock` payments provider for local dev and tests. |
| Auth | Email + password (argon2) with JWT access/refresh cookies. Google OAuth optional (feature flag). Email verification via Resend in prod, Mailpit in dev. |
| Licenses | MIT/Apache/OFL only in the product. Keep a `THIRD_PARTY.md`. |
| Tests | pytest (API + worker), Playwright (web e2e), plus the engine's `dev/smoke.py`. CI workflow runs all of them. |

If something here is impossible, stop and explain why, propose an alternative, and wait for the
owner's answer. For everything else, choose sensible defaults, write them down in `docs/DECISIONS.md`,
and keep going.

---

## 2. Repository layout (create this monorepo)

```
video-saas/
├── engine/                     # the folder plugins/video-studio/skills from video-studio.zip, verbatim
│   ├── video-engine/           # runtime/engine.js, scripts/vt.py, scripts/vtlib/, references/
│   ├── steps/ quiz/ mirror/ …  # 24 templates (template.js, template.json, examples/, SKILL.md)
│   └── video-studio/
├── engine-dev/                 # dev/ folder from the zip (smoke.py, mkplan.py, examples/, gen_skills.py)
├── apps/
│   ├── api/                    # FastAPI service
│   ├── worker/                 # RQ worker: pipeline, planner, providers
│   └── web/                    # Next.js app
├── packages/
│   └── shared/                 # plans/pricing config (YAML), template catalog JSON, OpenAPI types
├── infra/
│   ├── docker/                 # Dockerfiles: api, worker, web, (caddy for prod)
│   └── caddy/Caddyfile
├── docs/                       # ARCHITECTURE.md, DECISIONS.md, RUNBOOK.md, PROGRESS.md, THIRD_PARTY.md
├── .github/workflows/ci.yml
├── docker-compose.yml          # dev: postgres, redis, minio, mailpit, api, worker, web
├── docker-compose.prod.yml     # prod overrides: caddy, no minio/mailpit, restart policies, resource limits
├── .env.example
├── Makefile                    # make up / down / test / lint / migrate / seed / smoke
└── README.md
```

---

## 3. Engine facts you must know (read `engine/video-engine/SKILL.md` and `references/` for the rest)

- CLI: `python3 engine/video-engine/scripts/vt.py <cmd> JOB [...]`. Commands: `doctor`, `setup`,
  `templates`, `init` (requires `--template --lang --size`; refuses otherwise), `transcribe`, `tts`,
  `analyze`, `edit`, `media`, `stills`, `render`, `sfx`, `music`, `mix`, `mux`, `qa`, `build`.
- A job is a folder: `job.json`, `words.json`, `transcript.txt`, `analysis.txt`, `words_edit.json`,
  `transcript_edit.txt`, `edl.json`, `voice_edit.wav`, `cam_edit.mp4`, `media/`, `plan.json`,
  `cues.json`, `render/`, `sfx.wav`, `music.wav`, `mix.wav`, `final.mp4`, `qa/report.json`,
  `qa/contact_sheet.jpg`, `qa/final_sheet.jpg`.
- `plan.json` is the storyboard. Time anchors use word indices from `transcript_edit.txt`
  (`"w:12"`, `"we:12"`, `"w:12-0.1"`). The engine throws precise errors for a missing word index or an
  unknown scene type: use this as your validator.
- Each template has `template.json` (name, category, summary, scenes list, caption/music defaults),
  `SKILL.md` (scene schema + storyboard rules; this is the LLM's instruction manual) and
  `examples/plan.example.json` (with a `demoScript`; some also have `plan.ar.json`).
- `engine-dev/smoke.py` renders stills for every template at several sizes from the examples and
  reports browser errors. It must keep passing after any engine change.
- Fonts are downloaded from Google Fonts and cached under `~/.cache/video-studio/fonts`
  (`VT_CACHE` env var overrides the cache dir). Whisper models cache under `~/.cache/huggingface`.
- `vt.py mix`/`mux` produce the final MP4; there is no watermark support yet (you add it).
- `vt.py tts` uses edge-tts (you replace it).

---

## 4. Product scope (MVP)

**In:**
1. Sign up / log in / verify email / reset password.
2. New project wizard: upload (audio or video, ≤ 200 MB, ≤ 10 min) or paste a script (TTS only if
   the flag is on) → language (autodetect suggestion from transcription) → size (9:16, 1:1, 4:5,
   16:9, custom) → platform → template (start with **6 enabled**: `steps`, `mirror`, `quiz`, `chat`,
   `top-five`, `hot-take`; the other 18 exist in the catalog behind a per-template `enabled` flag)
   → optional **assets** (images and short clips, see item 9) → optional brief (title, key points,
   brand colors) → submit.
3. Pipeline: transcribe → analyze/edit → describe assets → LLM plan → preview stills → **user reviews
   and edits on-screen texts and asset placement** → render → final MP4 → download. Status updates live.
4. Credits: 1 credit = one rendered video up to 90 s (longer videos cost 1 credit per started
   90 s). Free plan: 2 credits/month, 720p, watermark. Paid plans: see `packages/shared/plans.yaml`.
5. Billing: Lemon Squeezy checkout, webhooks, customer portal link, plan changes, credit ledger.
6. Brand kit (v1: one per user): palette + display font + optional logo (logo shown in an end card
   only where a template supports `media`; otherwise ignored).
7. Admin: minimal CLI/admin endpoints to grant credits, toggle templates, view failed jobs.
8. Bilingual UI (en, ar with full RTL), responsive, accessible basics.
9. **Project assets (images and b-roll clips).** Per project the user can upload up to 20 assets
   (JPG, PNG incl. transparency, WebP, HEIC → converted; MP4/MOV clips ≤ 60 s; ≤ 25 MB per image,
   ≤ 100 MB per clip), each with an optional one-line description ("product photo", "my desk before").
   Assets without a description are auto-described by a vision model (fast model). The planner places
   assets in the scenes that talk about them (template media slots such as `top-five.rank.media`,
   `showcase.product.media`, `before-after.*.media`, `storytime.photo`, or the common full-frame `media`
   scene), anchored to the words that mention them. In the preview the user can swap an asset in a slot,
   remove it, or insert an unused asset as a full-frame `media` scene at a chosen moment. Unused assets
   are listed so the user sees what the AI left out.
10. **"Request a template" button**: a short form (what the video should look like, example link,
    optional file) stored in `template_requests`; admins list them. This drives the template roadmap.

**Out (do not build):** timeline editor, teams/seats, public API, mobile apps, stock footage,
social publishing.

---

## 5. Architecture

### 5.1 Services (docker compose)

| service | image | notes |
|---|---|---|
| `postgres` | postgres:16 | volume, healthcheck |
| `redis` | redis:7 | appendonly |
| `minio` (dev only) | minio/minio | bucket `videos` auto-created by an init container |
| `mailpit` (dev only) | axllent/mailpit | SMTP + web UI for emails |
| `api` | infra/docker/api.Dockerfile | FastAPI + uvicorn, runs migrations on start (`alembic upgrade head`) |
| `worker` | infra/docker/worker.Dockerfile | RQ worker(s); `WORKER_CONCURRENCY` replicas; non-root; `shm_size: 1g` for Chromium; CPU/memory limits in prod |
| `web` | infra/docker/web.Dockerfile | Next.js standalone build |
| `caddy` (prod only) | caddy:2 | TLS, reverse proxy to web + api |

All configuration via environment variables documented in `.env.example`. Secrets never in the repo.

### 5.2 Job state machine

```
created → uploading → queued_transcribe → transcribing → editing → planning → preview_ready
        → queued_render → rendering → done
any step → failed (with error_code + human message)      user actions: edit_texts, retry
```

Rules: each transition is written to `job_events`. Credits are **reserved** at `queued_render` and
**committed** at `done`, released on `failed`. Timeouts: transcribe 15 min, plan 5 min, render 30 min
(configurable). One automatic retry for transient failures (worker crash, timeout), none for user
errors (bad file). Jobs are idempotent: re-running a step must not corrupt the job folder.

### 5.3 Storage

Uploads go directly from the browser to S3 via presigned PUT (`inputs/{user}/{project}/{uuid}.{ext}`;
assets under `assets/{user}/{project}/{asset_id}.{ext}`). Assets follow the same lifecycle as inputs.
The worker downloads inputs into a scratch dir, runs the engine, uploads `final.mp4`, `contact_sheet.jpg`,
`final_sheet.jpg` and `plan.json` to `outputs/{user}/{project}/…`, then deletes scratch. Downloads use
short-lived presigned GET URLs. Lifecycle: inputs deleted 7 days after `done`; outputs kept 30 days on
free, 180 days on paid (a scheduled job enforces this).

### 5.4 LLM planner (the AI part, in `apps/worker/planner/`)

Inputs: template name, `engine/<template>/SKILL.md`, `engine/video-engine/references/plan-schema.md`,
`transcript_edit.txt`, the user brief, language, size, platform, brand kit, and the **asset list**
(`[{name: "asset_<id>", kind: image|clip, description, width, height, duration, has_alpha}]`).

Process:
1. Build a system prompt: role ("senior short-form video editor"), the template SKILL.md, the plan
   schema, hard rules (all on-screen text in the video language; use `labels` to translate template
   UI words; anchor every reveal to the word that says it; ≤ 6 words per card; never invent facts or
   statistics; keep the last scene ≥ 1.2 s after the last word).
2. User message: the indexed transcript, the brief, and one shortened example plan from the template's
   `examples/` (Arabic example if the video is Arabic and one exists).
3. Ask for **JSON only** (use provider JSON mode / tool calling where available; strip fences otherwise).
4. Validate: Pydantic schema (generic plan + per-template scene type whitelist from `template.json`),
   then **run `vt.py stills JOB --auto`** as the ground-truth validator. Any engine error → append the
   error to the conversation and ask for a fix. Max 3 attempts, then fail with `plan_failed`.
5. Optional (flag `PLANNER_VISION_REVIEW`): send `contact_sheet.jpg` to a vision-capable model with a
   checklist (text overflow, hidden text, wrong language/direction) and apply its fixes once.
6. Also produce `editable_fields`: a flat list of `{path, label, value, maxLen}` for every user-facing
   string in the plan, so the web app can render a simple "edit texts" form without knowing templates.
   Editing applies the values back by JSON path and re-runs stills.
7. Record model, tokens, cost estimate and attempts on the job.
8. **Assets:** before planning, run `describe_assets` (vision, fast model; one short line per asset,
   in the video language; skipped when the user wrote a description). The system prompt tells the model
   which scene fields accept media for the chosen template (derive the list from the template's SKILL.md
   scene table: fields named `media`) and the rules: use an asset only where the voice talks about it;
   never reuse the same asset in two slots unless asked; prefer transparent PNGs for product slots;
   put leftover but relevant assets in full-frame `media` scenes (≥ 1.5 s, anchored to a matching
   phrase); never invent asset names. Validation rejects unknown asset names. The planner returns
   `asset_slots`: `[{path, asset}]` so the web app can show and swap assets without knowing templates.
   Swapping or inserting an asset applies the change to `plan.json` and re-runs stills.

Providers: LiteLLM with `LLM_MODEL` (e.g. `anthropic/claude-sonnet-5`, `anthropic/claude-haiku-4-5-20251001`, `openai/gpt-4o`,
`gemini/gemini-2.5-pro`, `openrouter/<vendor>/<model>`, `groq/<model>`, `ollama/qwen2.5:14b`). Retries with backoff, per-request timeout, no streaming needed.
Model routing by task (env-configurable): `LLM_MODEL_PLANNER` (storyboard, default `anthropic/claude-sonnet-5`),
`LLM_MODEL_FAST` (edit decisions, label translation, editable-field labels; default `anthropic/claude-haiku-4-5-20251001`),
`LLM_MODEL_VISION` (contact-sheet review; default = planner model). Allow a per-plan override so free-tier
projects can use the fast model and paid projects the planner model (`PLANNER_MODEL_FREE`, `PLANNER_MODEL_PAID`).
Implementation requirements for provider independence:
- One `LLMClient` class wrapping LiteLLM: `complete_json(system, messages, schema, model, max_tokens, timeout)`.
  It handles JSON mode / tool calling where the provider supports it and falls back to "JSON only" prompting
  + fence stripping + one repair pass otherwise. Vision input goes through the same class.
- Provider keys from env: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`,
  `GROQ_API_KEY`, `OLLAMA_BASE_URL`. Missing key → that provider is listed as unavailable in `/admin/llm`.
- `app_settings` table (key/value jsonb) holds `llm.planner_model`, `llm.fast_model`, `llm.vision_model`,
  `llm.free_tier_model`, `llm.fallback_chain` (ordered list of models tried when the primary fails or
  times out). `GET/PUT /admin/llm` edits them; the worker reloads settings per job.
- Cost accounting uses LiteLLM's cost map when known, else a per-model price table in `plans.yaml`.
- Never hard-code a vendor name outside `LLMClient` and the settings defaults.
Write a **deterministic fallback planner** for `steps` and `mirror` (split the transcript into
sections on pauses, one scene per section, titles = first 4–6 words) used when the LLM is
unavailable, so the product never fully stops.

Also implement the **edit-decision step** with the LLM: given `analysis.txt` + transcript, return the
`--drop` ranges (stumbles, repeated takes). Validate ranges against word count; on any doubt drop nothing.

### 5.5 Engine changes you must make (keep `engine-dev/smoke.py` passing)

1. Remove `edge-tts`; add `TTSProvider` (OpenAI TTS implementation) behind `TTS_PROVIDER`; `vt.py tts`
   writes `tts.mp3` and the pipeline transcribes it for word timings.
2. Add `vt.py mux --watermark PATH --watermark-pos br --watermark-opacity 0.6` (PNG overlay via ffmpeg)
   and `--max-height 720` (downscale for the free plan).
3. Add `vt.py init --duration-limit 600` (refuse longer inputs) and `--job-timeout` awareness
   (the worker enforces timeouts, but the CLI should stop cleanly on SIGTERM).
4. Pre-cache fonts for all supported scripts during the worker image build (a script that runs
   `resolve_fonts` for each script with the roles used by all templates), so rendering works with no
   network. Make the render step run with network disabled (`--network none` semantics are not possible
   inside compose for a running container, so enforce it in code: `VT_OFFLINE=1` makes any network
   call fail fast instead of hanging).
5. Structured logs: `vt.py --json` prints one JSON object per log line.
6. Bake the whisper model into the image (`medium` in prod image, `small` in the test image).
7. Asset ingestion: `vt.py media` must accept HEIC/WebP (convert with Pillow + `pillow-heif`, strip
   EXIF after applying the rotation), keep PNG alpha (for product cut-outs use `object-fit: contain`
   via `--fit contain`), and for clips accept `--start/--duration` trimming and drop their audio unless
   `--keep-audio`. Add `vt.py assets JOB --manifest assets.json` that registers many assets in one call
   and writes `media/index.json` (name, kind, size, duration, alpha).

### 5.6 API (FastAPI) — main endpoints

```
POST /auth/register, /auth/login, /auth/logout, /auth/refresh, /auth/verify, /auth/forgot, /auth/reset
GET  /me                                   (plan, credits, brand kit)
PUT  /me/brand-kit
GET  /templates                            (catalog: enabled templates, sizes, platforms, languages)
POST /uploads/presign                      {filename, content_type, size} → {url, key}
POST /projects                             {title, input_key | script, lang, size, platform, template, brief} → job
GET  /projects, GET /projects/{id}, DELETE /projects/{id}
GET  /projects/{id}/events                 (SSE: state changes + progress %)
POST /projects/{id}/texts                  {fields:[{path,value}]} → re-run stills
POST /projects/{id}/assets/presign         {filename, content_type, size} → {url, key, asset_id}
POST /projects/{id}/assets                 {asset_id, description?} → registers an uploaded asset
GET  /projects/{id}/assets, PATCH /projects/{id}/assets/{asset_id} {description}, DELETE …
POST /projects/{id}/asset-slots            {changes:[{path, asset|null}], insert:[{asset, at_word, dur}]} → re-run stills
POST /template-requests                    {description, example_url?, file_key?}
POST /projects/{id}/render                 (reserves credits)
POST /projects/{id}/retry
GET  /projects/{id}/download               → presigned URL
GET  /billing/plans, POST /billing/checkout {plan} → checkout URL, GET /billing/portal
POST /billing/webhooks/lemonsqueezy        (signature verified, idempotent by event id)
GET  /health, GET /metrics (basic counters)
GET  /admin/llm, PUT /admin/llm             (model routing + fallback chain; lists available providers)
POST /admin/… (requires ADMIN_API_KEY): grant-credits, toggle-template, list-failed, list-template-requests
```

Every endpoint has request/response models, auth dependency, rate limiting (slowapi), and tests.

### 5.7 Database (Alembic migrations; write the DDL yourself, this is the shape)

- `users(id uuid pk, email unique, password_hash, email_verified_at, locale, plan, ls_customer_id, created_at, deleted_at)`
- `brand_kits(id, user_id fk unique, palette jsonb, fonts jsonb, logo_key, updated_at)`
- `projects(id, user_id fk, title, template, lang, size_w, size_h, platform, brief jsonb, status, progress int,
   input_key, input_kind, script text, plan jsonb, editable_fields jsonb, output_key, preview_key, sheet_key,
   duration_s numeric, credits_reserved int, credits_committed int, llm_model, llm_tokens_in, llm_tokens_out,
   llm_cost_usd numeric, error_code, error_message, attempts int, created_at, updated_at, done_at)`
- `project_assets(id uuid, project_id fk, user_id fk, kind enum(image, clip), key, original_name, mime, bytes,
   width, height, duration_s, has_alpha bool, description, description_source enum(user, ai), status, created_at)`
- `template_requests(id, user_id fk, description text, example_url, file_key, status, created_at)`
- `projects` also gets `asset_slots jsonb`.
- `job_events(id bigserial, project_id fk, from_status, to_status, detail jsonb, created_at)`
- `credit_ledger(id bigserial, user_id fk, delta int, reason enum(grant, plan_renewal, reserve, commit, release, refund, admin), project_id null fk, external_id null unique, created_at)`; balance = SUM(delta) with a fast path column on users updated in the same transaction.
- `subscriptions(id, user_id fk, provider, external_id unique, plan, status, current_period_end, cancel_at_period_end, raw jsonb, updated_at)`
- `webhook_events(id, provider, external_event_id unique, payload jsonb, processed_at, error)`
- `template_flags(name pk, enabled bool, tier_required)`
- `app_settings(key text pk, value jsonb, updated_at)` (LLM routing, feature flags)
- Indexes on `projects(user_id, created_at desc)`, `projects(status)`, `credit_ledger(user_id)`.

### 5.8 Web (Next.js)

Pages: `/` landing (bilingual, template gallery from `docs/previews`), `/login`, `/register`,
`/verify`, `/reset`, `/app` dashboard (projects list with status chips), `/app/new` (wizard,
direct-to-S3 upload with progress, client-side duration check via `<video>`/`<audio>` metadata),
`/app/projects/[id]` (status timeline, contact sheet preview, edit-texts form, **asset panel**:
thumbnails with descriptions, which slot each asset is in, swap/remove via a picker, "insert as full-screen
shot at…" with a word picker from the transcript, list of unused assets; render button, download, retry,
error explanation). The wizard gets an assets step (drag-and-drop multi-upload with per-file progress,
description field, HEIC preview via server thumbnail). A "Request a template" dialog is reachable from the
template picker, `/app/billing`, `/app/settings` (brand kit, locale, delete
account), `/pricing`, `/terms`, `/privacy`, `/refunds`.

Requirements: `next-intl` with `en` and `ar` messages files; `dir="rtl"` for Arabic; Tailwind logical
properties; loading and error states everywhere; no client-side secrets; API client generated from
OpenAPI (`openapi-typescript`); Playwright e2e tests for register → create project → preview → render
(with the mock LLM and small whisper) → download.

### 5.9 Billing rules

`packages/shared/plans.yaml` (single source of truth for API and web):

```yaml
free:    {price_usd: 0,  credits: 2,   max_res: 720,  watermark: true,  templates: basic}
starter: {price_usd: 15, credits: 15,  max_res: 1080, watermark: false, templates: basic}
pro:     {price_usd: 29, credits: 50,  max_res: 2160, watermark: false, templates: all, brand_kit: true}
agency:  {price_usd: 79, credits: 150, max_res: 2160, watermark: false, templates: all, brand_kit: true, priority_queue: true}
```

Credits renew on each successful subscription payment (webhook), unused credits do not roll over,
downgrade applies at period end. Webhooks are verified (HMAC), stored, processed exactly once.
`PAYMENTS_PROVIDER=mock` exposes `POST /billing/mock/subscribe` for dev and tests.

### 5.10 Security and limits

- Validate uploads with `ffprobe` on the worker (real audio/video stream, duration ≤ limit); reject others.
- Assets: verify real image/video content (Pillow open / ffprobe), max pixels 40 MP (decompression-bomb
  guard), per-project count and size limits enforced server-side, EXIF stripped on conversion.
- Worker runs as non-root, scratch dir per job, deleted after; `VT_OFFLINE=1` during render.
- Rate limits: auth endpoints 10/min/IP, project creation 10/hour/user (free) and 60/hour (paid).
- Max concurrent jobs per user: 1 (free), 3 (paid); priority queue for `agency`.
- Presigned URLs ≤ 15 min; content-type and size enforced by the presign policy.
- CORS locked to the web origin; secure, httpOnly cookies; CSRF token for cookie-auth POSTs.
- All LLM outputs are treated as untrusted data (validated JSON, HTML-escaped by the engine).
- `docs/RUNBOOK.md` covers backups (`pg_dump` nightly to S3), restore, rotating keys, scaling workers.

### 5.11 Observability

Structured JSON logs with `request_id`/`job_id`; `/health` checks DB, Redis, S3; basic Prometheus-style
counters (jobs by status, durations per step, LLM cost); Sentry DSN optional in both api and web;
`job_events` gives per-job timing for cost analysis.

---

## 6. Phases, tasks and Definition of done

Work phase by phase. At the end of each phase: run the full test suite, update `docs/PROGRESS.md`
(what was done, what was tested, what is open), commit with a clear message. If a phase reveals that
an earlier decision was wrong, fix it and record it in `docs/DECISIONS.md`.

### Phase 0 — Understand and verify the engine (½ day)
- Unzip the owner's `video-studio.zip`; move `plugins/video-studio/skills` → `engine/`, `dev/` → `engine-dev/`; fix the paths in `engine-dev/*.py` accordingly.
- Read `engine/video-engine/SKILL.md`, all `references/*.md`, `engine/steps/SKILL.md`, `engine/mirror/SKILL.md`.
- Build a throwaway worker image and run: `vt.py doctor`, `vt.py templates`, `engine-dev/smoke.py steps quiz --sizes 9:16,16:9`, and one full `vt.py build` with `--draft` on a smoke job.
- **DoD:** all of the above pass inside Docker; `docs/ARCHITECTURE.md` written with a diagram of §5; open questions listed for the owner.

### Phase 1 — Engine productisation (2.5 days)
- §5.5 changes (TTS provider, watermark/downscale, offline mode, font pre-cache, JSON logs, model baking, SIGTERM).
- `apps/worker/pipeline.py`: a Python module that runs a job end to end from a `JobSpec` (no Claude involved), with step functions, progress callbacks, timeouts, and a scratch dir.
- Test fixtures: generate speech offline with `espeak-ng` (install in the worker image) for 3 sentences in English; a synthetic screen recording via ffmpeg `testsrc2`.
- Asset ingestion (§5.5 item 7) with fixtures: a HEIC photo, a transparent PNG, a 90 s clip trimmed to 5 s.
- **DoD:** `pytest apps/worker` runs the pipeline on the espeak fixture with `small` whisper through transcribe → edit → deterministic fallback plan → stills → render (`--draft`) → mux with watermark, and asserts the MP4 exists, has audio, and QA report loudness is within ±2 LU of target. `engine-dev/smoke.py` (all templates, 9:16 + 16:9) passes in CI.

### Phase 2 — LLM planner (3 days)
- §5.4: prompt builder, provider abstraction (LiteLLM), JSON extraction, schema validation, engine validation loop, editable fields, cost accounting, vision review flag, fallback planner, edit-decision step.
- A `MockLLM` provider (returns the template's example plan re-anchored to the real transcript by a simple heuristic) for tests; a recorded-response test using a real provider is optional and skipped without an API key.
- Asset description + placement (§5.4 item 8), `asset_slots`, unknown-asset rejection.
- **DoD:** tests cover: valid plan accepted; plan with a bad word index gets repaired within 3 attempts (mock returns bad then good); unknown scene type rejected; unknown asset name rejected; editable fields and asset slots round-trip (edit/swap/insert → apply → stills); a `top-five` job with 5 fixture images (generated with Pillow) places each image in its rank and the contact sheet shows them (assert non-placeholder pixels in the media area). A manual run with a real model on the espeak fixture and on an Arabic sample (the owner will provide one) produces a plan that renders.

### Phase 3 — API and database (3.5 days)
- Compose services (postgres, redis, minio, mailpit, api, worker), Alembic migrations for §5.7, auth, uploads, projects, events (SSE), texts editing, render, retry, download, admin, health, rate limits.
- RQ queues: `transcribe`, `plan`, `render`, `priority`. Worker registers all; `agency` jobs go to `priority`.
- **DoD:** `pytest apps/api` (against a test Postgres in compose) ≥ 80 % coverage of routers and services; an integration test creates a user, uploads the espeak fixture to MinIO, creates a project with 3 image assets, waits for `preview_ready`, edits a text, swaps one asset, renders, downloads a valid MP4. Asset limits and invalid-file rejection are tested. `make up` on a clean machine works with only `.env.example` copied to `.env`.

### Phase 4 — Web app (4 days)
- §5.8 pages, i18n en/ar, direct uploads, SSE status, preview and edit form, render/download, billing pages with mock provider, settings/brand kit.
- **DoD:** Playwright e2e (register → new project with 2 image assets → preview → edit text → swap an asset → render → download) passes in CI headless against the compose stack with `MockLLM` and `small` whisper; Arabic locale renders RTL without layout breakage (screenshot test of 3 pages); Lighthouse accessibility ≥ 90 on landing and dashboard.

### Phase 5 — Billing, plans, limits (2 days)
- Lemon Squeezy provider (checkout URL creation, webhook verification, subscription lifecycle, portal link), credit ledger, renewals, plan gating (resolution, watermark, templates, concurrency), scheduled cleanup job, transactional emails (verify, reset, render done, payment failed).
- **DoD:** webhook tests with recorded payloads (created, updated, cancelled, payment_failed, order refunded) are idempotent and adjust credits correctly; credit reserve/commit/release tested under concurrent renders; free user gets 720p + watermark, paid does not.

### Phase 6 — Hardening and production (2 days)
- `docker-compose.prod.yml` + Caddy TLS; resource limits; backups; `docs/RUNBOOK.md`; Sentry; metrics; load test (10 concurrent jobs with `--draft`) documenting throughput per worker; security review checklist (§5.10) with each item verified; legal pages content placeholders; `README.md` with dev and deploy instructions.
- **DoD:** fresh VM deploy instructions followed literally work; all tests green in CI; `docs/PROGRESS.md` says "MVP complete" with the list of known limitations.

### Phase 7 — Mixed templates (post-MVP, start only after the owner confirms "MVP complete") (3–4 days)

Goal: one video can use scene types from several templates, so requests that do not fit a single
template still get a great result. Example: a `quiz:question`, then a `counter:stat`, then a
`whiteboard:list`, with one consistent look.

- **Engine:** `template.js` files register into a registry (`VT.template(def)` keyed by the template name)
  instead of replacing a single global. Plans gain `"template": "<base>"` (look: palette, fonts,
  background, overlays, captions, transitions come only from the base) and `"mix": ["quiz", "counter", …]`.
  Scene types are namespaced `"<template>:<scene>"`; un-namespaced types resolve to the base. When a mixed
  scene runs, palette keys shared by all templates (`bg`, `deep`, `ink`, `paper`, `accent`, `text`, `muted`)
  come from the base palette; template-specific keys (`myth`, `fact`, `gold`, …) keep that template's
  defaults unless overridden in the plan. Overlays of non-base templates are not loaded. `render.py`
  injects all needed `template.js` files and loads the union of font roles. Single-template plans must
  behave exactly as before (regression: smoke tests unchanged).
- **Contrast safety:** add `VT.contrast(fg, bg)` and a render-time check that warns (stills report) when
  a mixed scene's text/background contrast is below WCAG AA; the planner fixes it via palette overrides.
- **Planner:** a `mixed` mode that receives the base template's full SKILL.md plus only the scene tables
  (not the full docs) of up to 6 candidate templates chosen by a cheap pre-step (fast model picks
  candidates from the catalog summaries given the transcript). Same validation loop.
- **Product:** a "Smart mix (AI picks the scenes)" option in the template picker, paid plans only, flag
  `mixed_templates`. Template requests (MVP item 10) are reviewed to decide which new scene types to add.
- **Tests:** mixed example plans (≥ 3, including an Arabic one) in `engine-dev/examples/`, smoke-tested at
  9:16, 1:1, 16:9; planner tests with the mock; one e2e flow with "Smart mix".
- **DoD:** all existing smoke tests unchanged and green; mixed examples render without browser errors,
  with no contrast warnings; `docs/PROGRESS.md` updated.

---

## 7. Engineering standards

- Small, reviewed-quality commits; conventional commit messages; a `CHANGELOG.md`.
- Type hints everywhere; `ruff` + `mypy` (api/worker), `eslint` + `tsc --noEmit` (web) in CI.
- No TODOs without an issue-style note in `docs/PROGRESS.md`.
- Errors are typed (`error_code`) and mapped to user-friendly, translated messages in the web app.
- Never log secrets, tokens or full transcripts at INFO level.
- Anything that talks to the network has a timeout and a retry policy.
- Tests must be runnable with `make test` and in CI; flaky tests are bugs.
- When you change engine behaviour, add or update an example plan and re-run the smoke test.
- Keep the engine's CLI backward compatible; the skills' `SKILL.md` files must still be true.

## 8. How to work with the owner

- Start by confirming you have the zip, then do Phase 0. Report with a short summary and the open
  questions. Ask only what blocks you; otherwise pick a default and document it.
- Default answers to expected questions: product name placeholder `VideoStudio` (configurable
  `APP_NAME`), default LLM `anthropic/claude-sonnet-5` if `ANTHROPIC_API_KEY` is set, otherwise
  `openai/gpt-4o`, otherwise `ollama/qwen2.5:14b`; default locale English; default currency USD.
- At the end of every phase: what was built, how it was tested (with the actual commands and their
  output summarised), what is next, and anything the owner must do (create accounts, provide keys,
  provide an Arabic sample recording).
- Never claim something works without having run it. If you could not run something (e.g. no API key,
  no internet), say so explicitly and leave a test that is skipped with a clear reason.

## 9. Deliverables checklist (MVP complete)

- [ ] `docker compose up` brings up the full stack; `make test` is green; CI is green
- [ ] Engine changes merged; `engine-dev/smoke.py` passes for all 24 templates at 9:16 and 16:9
- [ ] LLM planner with validation loop, fallback planner, editable fields, asset placement, cost tracking
- [ ] Project assets: upload, auto-description, placement, swap/insert in preview; template requests
- [ ] API with auth, uploads, projects, SSE, billing, admin; ≥ 80 % router coverage
- [ ] Web app bilingual (en/ar RTL), e2e tests passing
- [ ] Billing with Lemon Squeezy + mock provider, credit ledger, plan gating, watermark
- [ ] Production compose with TLS, backups, runbook, monitoring
- [ ] `docs/`: ARCHITECTURE, DECISIONS, RUNBOOK, PROGRESS, THIRD_PARTY; `README.md`

Start with Phase 0 now.
