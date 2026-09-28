# VideoStudio SaaS

A web app that turns a voice note, a talking-head video or a script into a finished, professionally
edited short video: animated scenes synced to every spoken word, captions, sound effects, music and
mastered audio. Any language, any aspect ratio. Free tier with watermark, paid plans with credits.

The rendering engine (24 templates + `video-engine`) lives in `engine/` and is driven through its CLI,
`python3 engine/video-engine/scripts/vt.py`. Everything else (API, queue, workers, LLM planner, web
app, billing) wraps it. See `VIDEO_STUDIO_SAAS_BRIEF.md` for the brief and `docs/` for architecture,
decisions and progress.

## Status

Phases 0–3 are done: engine verified in Docker, engine productised, worker pipeline, LLM planner (LiteLLM, all providers) with mock, API + database + queues + compose stack.
See `docs/PROGRESS.md` for what was tested and what is open, `CHANGELOG.md` for the change list.

## Run the stack

```bash
cp .env.example .env            # defaults work locally; add an LLM key to get real storyboards (otherwise the fallback planner runs)
make up                         # postgres, redis, minio (+bucket), mailpit, api (migrations on start), worker
open http://localhost:8000/docs # API docs · MinIO console :9101 · Mailpit :8025
make test-api                   # API unit tests (needs only postgres/redis/minio/mailpit)
make test-api-integration       # full flow with the worker and the mock planner
make seed                       # admin@example.com / admin-password-123 on the pro plan with 50 credits
```

## Developer workflow (everything runs in Docker)

```bash
make worker-image                 # build vs-worker:dev (WHISPER_MODEL=small; pass WHISPER_MODEL=medium for prod)
make test-worker                  # pytest apps/worker inside the image (engine CLI, assets, planner, mux, TTS, full pipeline)
make smoke                        # engine stills smoke test for a few templates, offline
make smoke-all                    # all 24 templates at 9:16 + 16:9, offline (what CI runs)
make e2e                          # LLM-free espeak → whisper → edit → plan → build --draft into ./jobs/smoke
make lint-worker                  # ruff + mypy
make plan-run INPUT=voice.m4a TEMPLATE=steps LANG=ar   # real-model run (needs a provider key in .env or the environment)
```

LLM providers: set one of `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `GROQ_API_KEY`, `OLLAMA_BASE_URL`.
Routing: `LLM_MODEL_PLANNER`, `LLM_MODEL_FAST`, `LLM_MODEL_VISION`, `PLANNER_MODEL_FREE`, `PLANNER_MODEL_PAID`, `LLM_FALLBACK_CHAIN`,
`PLANNER_VISION_REVIEW`. `PLANNER_MODE=mock|fallback` avoids any provider. `python -m vs_worker.cli providers` shows what is available.

Engine CLI cheatsheet (inside the image, `python3 /app/engine/video-engine/scripts/vt.py …`):

```bash
vt.py --json init JOB --template steps --lang en --size 9:16 --input voice.m4a --duration-limit 600
vt.py transcribe JOB --model small && vt.py analyze JOB && vt.py edit JOB
vt.py assets JOB --manifest assets.json           # HEIC/WebP/PNG(alpha)/clips → media/index.json
vt.py stills JOB --auto                           # validator + contact sheet
VT_OFFLINE=1 vt.py build JOB --draft --watermark packages/shared/assets/watermark.png --max-height 720
```

## Layout

```
engine/          the engine and 24 templates (verbatim from video-studio.zip)
engine-dev/      smoke.py, e2e_build.py, mkplan.py, gen_skills.py
apps/            api (FastAPI), worker (RQ), web (Next.js)        [phases 1–4]
packages/shared  plans.yaml, template catalog, OpenAPI types      [phase 3]
infra/           Dockerfiles, Caddy
docs/            ARCHITECTURE.md, DECISIONS.md, PROGRESS.md, previews/
```
