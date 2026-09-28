# Architecture

VideoStudio (placeholder name, `APP_NAME`) wraps the existing Video Studio rendering engine in a
production SaaS: a FastAPI API, a Redis/RQ job queue, Python workers that run the engine CLI, an LLM
storyboarding step, a Next.js web app, Lemon Squeezy billing, all delivered with Docker Compose.

The engine is **not rewritten**. It lives verbatim under `engine/` (24 templates + `video-engine/`)
and is driven only through its CLI contract (`python3 engine/video-engine/scripts/vt.py <cmd> JOB`).

## 1. Repository layout

```
engine/            24 template folders + video-engine/ (vt.py, vtlib/, runtime/, references/)
engine-dev/        smoke.py, mkplan.py, gen_skills.py, skilldata.py, examples/  (paths point at ../engine)
apps/api/          FastAPI service (auth, uploads, projects, SSE, billing, admin)
apps/worker/       RQ worker: pipeline.py (engine driver), planner/ (LLM), providers/ (LLM, TTS, storage)
apps/web/          Next.js 15 app (en/ar, RTL)
packages/shared/   plans.yaml, template catalog JSON, OpenAPI-generated types
infra/docker/      api.Dockerfile, worker.Dockerfile, web.Dockerfile, caddy
docs/              this file, DECISIONS.md, PROGRESS.md, RUNBOOK.md, THIRD_PARTY.md, previews/
```

## 2. System diagram

```
                       ┌────────────────────────────────────────────────────────────────┐
                       │                        docker compose                          │
   browser             │                                                                │
 ┌──────────┐  HTTPS   │  ┌──────────┐   /api/*   ┌──────────────┐    SQL     ┌───────┐ │
 │ Next.js  │◄────────►│  │  caddy   │──────────►│  api (FastAPI)│◄──────────►│postgres│ │
 │ (web)    │          │  │ (prod)   │──────────►│  uvicorn      │            └───────┘ │
 └────┬─────┘          │  └──────────┘   /*      │  alembic      │    RQ enqueue        │
      │ presigned PUT/GET               ┌───────►│  SSE /events  │──────────┐           │
      │                                 │        └──────┬────────┘          ▼           │
      │                                 │               │ health      ┌──────────┐      │
      ▼                                 │               ▼             │  redis   │      │
 ┌──────────────┐                       │        ┌──────────────┐     │ queues:  │      │
 │ S3 storage   │◄──────────────────────┼────────│  worker (RQ) │◄────│transcribe│      │
 │ MinIO (dev)  │  inputs/ assets/      │        │  pipeline.py │     │plan      │      │
 │ R2 (prod)    │  outputs/             │        │  planner/    │     │render    │      │
 └──────────────┘                       │        │  vt.py CLI   │     │priority  │      │
                                        │        │  Chromium    │     └──────────┘      │
                                        │        │  ffmpeg      │                       │
                                        │        │  whisper     │──► LiteLLM ──► Anthropic / OpenAI / Gemini /
                                        │        └──────────────┘                OpenRouter / Groq / Ollama
                                        │                                                │
                                        │  ┌──────────┐ SMTP  ┌────────────┐              │
                                        │  │ mailpit  │◄──────│ api emails │  (dev)       │
                                        │  └──────────┘       └────────────┘  Resend (prod)│
                       └────────────────────────────────────────────────────────────────┘
   Lemon Squeezy ──webhooks (HMAC)──► api /billing/webhooks/lemonsqueezy ──► credit_ledger, subscriptions
```

## 3. Services

| service | image | role |
|---|---|---|
| `postgres` | postgres:16 | system of record (users, projects, ledger, events, settings) |
| `redis` | redis:7 (appendonly) | RQ queues `transcribe`, `plan`, `render`, `priority`; rate-limit counters |
| `minio` (dev) | minio/minio | S3-compatible bucket `videos` (init container creates it) |
| `mailpit` (dev) | axllent/mailpit | SMTP sink + web UI |
| `api` | infra/docker/api.Dockerfile | FastAPI, runs `alembic upgrade head` on start |
| `worker` | infra/docker/worker.Dockerfile | RQ worker: ffmpeg, Playwright Chromium, faster-whisper (model baked), fonts pre-cached, espeak-ng (tests); non-root; `shm_size: 1g` |
| `web` | infra/docker/web.Dockerfile | Next.js standalone |
| `caddy` (prod) | caddy:2 | TLS + reverse proxy |

## 4. Job pipeline and state machine

```
created → uploading → queued_transcribe → transcribing → editing → planning → preview_ready
        → queued_render → rendering → done
any step → failed (error_code + message)          user actions: edit_texts, swap assets, retry
```

Each transition is a row in `job_events`. Credits are reserved at `queued_render`, committed at `done`,
released on `failed`. Timeouts: transcribe 15 min, plan 5 min, render 30 min. One automatic retry
for transient failures, none for user errors. Steps are idempotent on the job folder.

Worker step → engine command mapping:

| pipeline step | engine commands | outputs read back |
|---|---|---|
| transcribe | `init --input`, `transcribe --model` | `words.json`, `transcript.txt` (detected language) |
| edit | `analyze`, LLM edit-decision → `edit --drop …`, `media --name cam` (video input) | `transcript_edit.txt`, `words_edit.json`, `edl.json`, `cam_edit.mp4` |
| assets | `assets JOB --manifest assets.json` (new, Phase 1) | `media/index.json` |
| plan | LLM planner → `plan.json`; validate with `stills --auto` | `qa/contact_sheet.jpg`, `editable_fields`, `asset_slots` |
| render | `render --draft?`, `sfx`, `music`, `mix`, `mux --watermark --max-height`, `qa` | `final.mp4`, `qa/report.json`, `qa/final_sheet.jpg` |

The worker downloads inputs into a per-job scratch directory, runs the engine with `VT_OFFLINE=1`
during render, uploads `final.mp4`, `contact_sheet.jpg`, `final_sheet.jpg`, `plan.json` to
`outputs/{user}/{project}/…`, then deletes the scratch directory.

## 5. Storage layout (S3)

```
inputs/{user}/{project}/{uuid}.{ext}          presigned PUT from the browser (≤ 200 MB, ≤ 10 min)
assets/{user}/{project}/{asset_id}.{ext}      up to 20 per project (images ≤ 25 MB, clips ≤ 100 MB / 60 s)
outputs/{user}/{project}/final.mp4 | contact_sheet.jpg | final_sheet.jpg | plan.json
```
Lifecycle: inputs deleted 7 days after `done`; outputs 30 days (free) / 180 days (paid).

## 6. LLM planner (apps/worker/vs_worker/planner/, llm/)

```
transcript_edit.txt + brief + template SKILL.md + plan-schema.md + asset list (media/index.json)
        │
        ▼
 prompts.build_system_prompt / build_user_message
        │
        ▼
 LLMClient.complete_json  (LiteLLM: anthropic | openai | gemini | openrouter | groq | ollama; JSON mode or JSON-only + repair pass;
        │                  fallback chain; timeout; cost via LiteLLM map or plans.yaml)
        ▼
 schema.validate_plan  (Pydantic shape, scene whitelist from template.json, anchors < n_words, asset names ⊆ registered media)
        │  ok
        ▼
 PlanContext.validate → pipeline writes plan.json and runs `vt.py stills --auto`  ──► qa/contact_sheet.jpg
        │  engine errors appended to the conversation, ≤ 3 attempts, then error `plan_failed`
        ▼
 optional vision review (PLANNER_VISION_REVIEW): contact sheet + checklist → text fixes applied once by path, re-validated
        │
        ├─► editable_fields [{path,label,value,maxLen}]        (schema.editable_fields; apply with Pipeline.apply_texts)
        ├─► asset_slots     [{path, asset}] + unused_assets     (schema.asset_slots;  apply with Pipeline.apply_assets)
        └─► job.json: planner, llm {model, tokens_in/out, cost_usd, calls, attempts, by_task}, plan_attempts
 LLM unreachable → planner.fallback (deterministic) so the job still reaches preview_ready
```

Other LLM-backed steps, both optional and conservative: `planner.edit_decision` (fast model proposes `--drop` word ranges for
`vt.py edit`; validated, drop nothing on doubt) and `planner.assets.AssetDescriber` (vision model writes one line per asset without a
user description). Model routing (`LLMSettings`): `llm.planner_model`, `llm.fast_model`, `llm.vision_model`, `llm.free_tier_model`,
`llm.fallback_chain` from env defaults, overridable per job with the `app_settings` rows (Phase 3, `GET/PUT /admin/llm`).
Tests use `MockLLM` (example plan re-anchored to the transcript, scripted failures) and a fake transport under `LLMClient` for each
provider; `tests/test_llm_real.py` hits real providers when their key is present.

## 7. Engine facts that shape the design (verified in Phase 0)

- `vt.py init` refuses to run without `--template --lang --size` (`die()` exits 2 with a clear message).
- Time anchors resolve in `engine.js` (`ref()`): a missing word index throws
  `Plan references missing word index w:N (have M words)`; an unknown scene type throws
  `Scene type "x" is not defined by this template. Available: …`. These surface through `stills`
  as a non-zero exit with the message in stderr, which is what the planner's validation loop consumes.
- Scenes shorter than 0.6 s are returned as `warnings` from `__init` (not errors).
- Media is registered in `job.json` under `media.<name>` as `file://` URIs (image) or a JPG frame
  sequence directory (video). Templates draw a placeholder when a named media is missing, so a plan
  referencing an unknown asset does **not** fail in the engine: the planner must validate asset
  names itself.
- Media-accepting fields per template (from the SKILL.md scene tables): common `media.media`;
  `before-after.compare.before.media/after.media`; `breaking.headline.media`; `cinema.shot.media`;
  `city-map.place.media`; `flash-sale.items[].media`; `podcast.solo.media`; `review.score.media`;
  `screen.demo.media`; `storytime.photo.media`; `showcase.product.media`; `recipe.title/step/final.media`;
  `top-five.rank.media`; `workout.exercise.media`. `mirror`/`storytime` expect `cam`.
- Fonts come from Google Fonts at render time and are cached under `VT_CACHE/fonts`; without network
  the engine falls back to system fonts silently (`font 'X' unavailable (offline?)`). Phase 1 pre-caches
  all script/role combinations in the image and makes `VT_OFFLINE=1` fail fast on any network call.
- `vt.py` module-level constants: `SKILLS_DIR = ENGINE_DIR.parent`, so templates must stay siblings of
  `video-engine/` (they do under `engine/`).
- `vt.py tts` is edge-tts based (unofficial Microsoft endpoint) and is removed in Phase 1.
- `mix`/`mux`: no watermark or downscale yet (added in Phase 1 as `mux --watermark … --max-height`).
- `qa` flags loudness off target by more than 1.5 LU, true peak above -0.5 dBTP, black frames, and wrong
  resolution.
- `transcribe` defaults to whisper `medium`; the worker passes `--model` explicitly (`small` in tests).
- The renderer uses `page.screenshot` per frame piped to ffmpeg (mjpeg → libx264 crf 17), parallelised
  across N Chromium pages; `--draft` renders at half scale.
