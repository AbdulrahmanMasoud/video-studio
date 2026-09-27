# VideoStudio SaaS

A web app that turns a voice note, a talking-head video or a script into a finished, professionally
edited short video: animated scenes synced to every spoken word, captions, sound effects, music and
mastered audio. Any language, any aspect ratio. Free tier with watermark, paid plans with credits.

The rendering engine (24 templates + `video-engine`) lives in `engine/` and is driven through its CLI,
`python3 engine/video-engine/scripts/vt.py`. Everything else (API, queue, workers, LLM planner, web
app, billing) wraps it. See `VIDEO_STUDIO_SAAS_BRIEF.md` for the brief and `docs/` for architecture,
decisions and progress.

## Status

Phase 0 (engine verified inside Docker) is complete. See `docs/PROGRESS.md`.

## Quick engine check (Phase 0)

```bash
docker build -f infra/docker/worker.Dockerfile -t vs-worker:dev .          # WHISPER_MODEL=small by default
docker run --rm vs-worker:dev python3 /app/engine/video-engine/scripts/vt.py doctor
docker run --rm vs-worker:dev python3 /app/engine/video-engine/scripts/vt.py templates
docker run --rm --shm-size=1g -v "$PWD/engine-dev/_smoke:/out" vs-worker:dev \
    python3 /app/engine-dev/smoke.py steps quiz --sizes 9:16,16:9 --out /out
docker run --rm --shm-size=1g -v "$PWD/jobs:/jobs" vs-worker:dev \
    python3 /app/engine-dev/e2e_build.py /jobs/smoke --draft                  # espeak → whisper → edit → plan → build
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
