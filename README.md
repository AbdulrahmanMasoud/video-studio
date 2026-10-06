# VideoStudio

Turn a voice note, a talking-head video or a script into a finished short video: animated scenes synced to every spoken word,
captions, sound effects, music and mastered audio. Any language (Arabic and other RTL scripts included), any aspect ratio.
Free tier with a watermark, paid plans with credits.

The rendering engine (24 templates + `video-engine`) lives in `engine/` and is driven through its CLI. Everything else wraps it:
a FastAPI API, a Redis/RQ worker that runs the engine, an LLM storyboard planner (any provider through LiteLLM), a bilingual
Next.js web app, Lemon Squeezy billing, all delivered with Docker Compose.

```
browser ──► Next.js (web) ──► FastAPI (api) ──► Postgres / Redis / S3
                                   │
                                   └──► RQ worker: whisper → clean edit → LLM storyboard → Chromium render → ffmpeg mix → MP4
```

## Quick start (local, 10 minutes)

Requirements: Docker Desktop (or Docker Engine) with about 8 GB of memory, 15 GB of disk, and `make`.

```bash
git clone <this repo> videostudio && cd videostudio
cp .env.example .env          # defaults work locally; see "Keys" below for the optional ones
make up                       # builds the images (first time ~15 min) and starts everything
```

Then open:

| what | where |
|---|---|
| the app | http://localhost:3000 |
| API docs (OpenAPI) | http://localhost:8000/docs |
| emails sent by the app (Mailpit) | http://localhost:8025 |
| object storage console (MinIO) | http://localhost:9101 (user `videostudio`, password `videostudio-secret`) |

Stop with `make down`. Logs with `make logs`.

## Using the app

1. **Create an account** at http://localhost:3000/en/register (Arabic UI at `/ar`). The verification email lands in Mailpit; in
   development you can use the app without verifying.
2. **New video**: upload a voice note or a camera video (up to 200 MB, 10 minutes). Pick the language (or let it detect), the size
   (9:16, 1:1, 4:5, 16:9 or custom), the platform, and a template. Optionally add images and clips with a one-line description each,
   and a brief (title, key points, brand colors).
3. **Preview**: in about a minute the project shows a contact sheet, one frame per scene. Edit any on-screen text, swap or remove
   your images in their scenes, or insert an unused image as a full-screen shot at a chosen word. Every edit refreshes the preview.
4. **Render** (uses credits: 1 per started 90 seconds) and **download** the MP4. The free plan renders at 720p with a watermark.
5. **Billing**: in development the checkout is a mock; "Choose Pro" switches the plan instantly. With Lemon Squeezy keys it becomes a
   real hosted checkout.

Without an LLM key the storyboard comes from a deterministic fallback planner (plain but valid). Add a key for AI storyboards:

```bash
# .env
ANTHROPIC_API_KEY=sk-ant-...      # or OPENAI_API_KEY / GEMINI_API_KEY / OPENROUTER_API_KEY / GROQ_API_KEY / OLLAMA_BASE_URL
make up
```

AI voice from a pasted script is off by default; enable with `TTS_ENABLED=1`, `TTS_PROVIDER=openai` and an OpenAI key.

## Keys and configuration

Everything is configured in `.env` (never committed). `docs/CREDENTIALS.md` lists every key, where to get it, and the Lemon
Squeezy setup step by step. The important ones:

| key | purpose |
|---|---|
| `ANTHROPIC_API_KEY` (or another provider) | AI storyboards; `LLM_MODEL_*` for routing, editable at runtime via `PUT /admin/llm` |
| `PAYMENTS_PROVIDER=lemonsqueezy` + `LEMONSQUEEZY_*` | real billing (mock otherwise) |
| `EMAIL_PROVIDER=resend` + `RESEND_API_KEY` | production email (Mailpit otherwise) |
| `S3_*` | Cloudflare R2 or any S3 in production (MinIO otherwise) |
| `SECRET_KEY`, `ADMIN_API_KEY` | must be random in production |

Admin operations (grant credits, enable templates, change LLM routing, list failed jobs and webhooks) are HTTP endpoints under
`/admin/*` authenticated with the `X-Admin-Key` header. Examples are in `docs/RUNBOOK.md`.

## Deploy to production

One VM with Docker: follow `docs/RUNBOOK.md`, fill `.env` from `docs/CREDENTIALS.md`, then

```bash
make prod-up        # Caddy with automatic TLS, api, worker, web, nightly backups; no MinIO/Mailpit
make prod-logs
make backup-now
```

## Developer workflow (everything runs in Docker)

```bash
make test               # worker + API suites
make test-worker        # engine CLI, assets, planner, mux, TTS, full pipeline (inside the worker image)
make test-api           # API unit tests against Postgres/Redis/MinIO/Mailpit (93 % coverage)
make test-api-integration   # register → upload → assets → preview → edit → swap → render → download, with the worker
make test-web           # Playwright: the same flow in the browser + Arabic RTL + axe
make lighthouse         # accessibility gate (landing and dashboard)
make smoke-all          # every template renders stills at 9:16 and 16:9, offline
make loadtest           # 10 concurrent jobs through the API
make web-dev            # Next.js dev server on the host (node 22)
make plan-run INPUT=voice.m4a TEMPLATE=steps LANG=ar    # one job with the LLM planner from the command line
```

Engine CLI (inside the worker image, `python3 /app/engine/video-engine/scripts/vt.py …`): `doctor`, `templates`, `init`,
`transcribe`, `tts`, `analyze`, `edit`, `media`, `assets`, `stills`, `render`, `sfx`, `music`, `mix`, `mux`, `qa`, `build`.
`--json` gives one JSON object per log line; `VT_OFFLINE=1` makes network calls fail fast. See `engine/video-engine/SKILL.md`.

## Repository layout

```
engine/          the engine and 24 templates (verbatim from video-studio.zip, plus Phase 1 changes)
engine-dev/      smoke.py, e2e_build.py, gen_catalog.py, mkplan.py
apps/api/        FastAPI: auth, uploads, projects, assets, billing, admin, SSE, metrics (+ Alembic migrations)
apps/worker/     RQ worker: pipeline, LLM planner, providers, tasks
apps/web/        Next.js 15 app (en/ar, RTL), Playwright e2e, Lighthouse
packages/shared/ plans.yaml, templates.json, watermark
infra/           Dockerfiles, Caddyfile, backup and load-test scripts, postgres init
docs/            ARCHITECTURE, DECISIONS, PROGRESS, RUNBOOK, SECURITY, CREDENTIALS, THIRD_PARTY, previews/
```

## Documentation

- `VIDEO_STUDIO_SAAS_BRIEF.md`: the brief this was built from.
- `docs/PROGRESS.md`: what each phase delivered, how it was tested, known limitations.
- `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/RUNBOOK.md`, `docs/SECURITY.md`, `docs/CREDENTIALS.md`, `docs/THIRD_PARTY.md`.
- `CHANGELOG.md`.

## License

The engine is MIT (see `engine/LICENSE`). Third-party components and their licenses are listed in `docs/THIRD_PARTY.md`.
