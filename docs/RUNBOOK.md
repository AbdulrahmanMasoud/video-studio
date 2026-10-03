# Runbook

Operational procedures for a single-VM deployment with Docker Compose. Everything below assumes the repo is checked out at
`/opt/videostudio` on the server and `.env` is filled in (see `docs/CREDENTIALS.md`).

## Deploy on a fresh VM (Ubuntu 24.04, 4 vCPU / 8 GB recommended, 60 GB disk)

```bash
# 1. Docker
curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER && newgrp docker
# 2. Code + config
sudo mkdir -p /opt/videostudio && sudo chown $USER /opt/videostudio && cd /opt/videostudio
git clone <your repo url> . && cp .env.example .env
#    edit .env: SECRET_KEY, ADMIN_API_KEY, POSTGRES_PASSWORD, DATABASE_URL*, S3_* (R2), EMAIL_PROVIDER=resend + RESEND_API_KEY,
#    PAYMENTS_PROVIDER=lemonsqueezy + LEMONSQUEEZY_*, ANTHROPIC_API_KEY (or another LLM key),
#    APP_ENV=prod, COOKIE_SECURE=1, WEB_ORIGIN=https://app.example.com, API_BASE_URL=https://app.example.com/api,
#    S3_PUBLIC_ENDPOINT_URL=<R2 public endpoint>, DOMAIN=app.example.com, ACME_EMAIL=you@example.com, WHISPER_MODEL=medium
# 3. DNS: A/AAAA record for DOMAIN → the VM. Ports 80/443 open.
# 4. Build and start (first build ~15 min: whisper medium + fonts + Chromium)
make prod-up
# 5. Check
curl -s https://app.example.com/health          # {"status":"ok",...}
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps
```

`make prod-up` = `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`. Migrations run on API start.
Caddy obtains the TLS certificate automatically. MinIO and Mailpit are not started in prod (profiles).

## Day-2 operations

| task | command |
|---|---|
| logs | `make prod-logs` (api + worker + caddy) |
| update to a new version | `git pull && make prod-up` (rolling: api/web restart in seconds; workers finish their current job because RQ jobs are time-limited and the container gets SIGTERM → the CLI exits cleanly, the job is retried once) |
| scale workers | `WORKER_CONCURRENCY=4 make prod-up` (each worker needs ~2–4 GB RAM at 1080p, 1 CPU per Chromium page; set `RENDER_WORKERS` accordingly) |
| grant credits | `curl -X POST https://app.example.com/api/admin/grant-credits -H "X-Admin-Key: $ADMIN_API_KEY" -H 'Content-Type: application/json' -d '{"email":"user@example.com","credits":10,"note":"support"}'` |
| enable a template | `… /api/admin/toggle-template -d '{"name":"recipe","enabled":true,"tier_required":"pro"}'` |
| change LLM routing without redeploy | `curl -X PUT …/api/admin/llm -d '{"planner_model":"openai/gpt-4o","fallback_chain":["anthropic/claude-sonnet-5"]}'` |
| see failed jobs | `GET /api/admin/failed`; retry from the UI or `POST /api/projects/{id}/retry` as the user |
| see webhook deliveries | `GET /api/admin/webhooks` |
| metrics | `GET /api/metrics` (Prometheus text; scrape with your Prometheus/Grafana) |
| queue sizes | included in `/metrics` (`vs_queue_size`) or `docker compose exec redis redis-cli llen rq:queue:render` |

## Backups

The `backup` service runs `pg_dump` every day at `BACKUP_HOUR_UTC` (default 03:00) and uploads `backups/videostudio-<stamp>.sql.gz` to the
S3 bucket, keeping `BACKUP_KEEP_DAYS` (14). Run one now: `docker compose -f docker-compose.yml -f docker-compose.prod.yml run --rm backup once`.
Object storage (inputs/outputs/assets) is not duplicated: enable bucket versioning or lifecycle rules at your provider if you need that.

### Restore

```bash
aws --endpoint-url $S3_ENDPOINT_URL s3 cp s3://$S3_BUCKET/backups/videostudio-<stamp>.sql.gz /tmp/
docker compose -f docker-compose.yml -f docker-compose.prod.yml stop api worker
gunzip -c /tmp/videostudio-<stamp>.sql.gz | docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB
docker compose -f docker-compose.yml -f docker-compose.prod.yml start api worker
```
For a point-in-time move to a new VM: restore the dump, point `S3_*` at the same bucket, start the stack.

## Rotating keys

| key | how |
|---|---|
| `SECRET_KEY` | change in `.env`, `make prod-up`. Every session and pending email link becomes invalid (users sign in again). |
| `ADMIN_API_KEY` | change in `.env`, restart api. |
| S3 keys | create the new token at the provider, update `S3_ACCESS_KEY/S3_SECRET_KEY`, restart api + worker + backup, then revoke the old token. Presigned URLs already issued stay valid until they expire (≤ 15 min). |
| Lemon Squeezy API key / webhook secret | create the new one in the dashboard, update `.env`, restart api; for the webhook secret update the webhook in the dashboard at the same time. |
| LLM keys | update `.env`, restart worker (the worker reads keys at job start). |
| Postgres password | `ALTER USER videostudio PASSWORD '…'` then update `.env` and restart api/worker/backup. |

## Incidents

| symptom | check | fix |
|---|---|---|
| `/health` reports `s3: error` | credentials, endpoint, bucket exists | fix `.env`, `make prod-up` |
| jobs stuck in `queued_*` | `docker compose ps worker`, `vs_queue_size` in metrics | restart worker; the job is retried once automatically on worker crash |
| renders fail with `engine_error … Target crashed` | worker memory | lower `RENDER_WORKERS` (1), raise the worker memory limit |
| storyboards always "automatic fallback" | `GET /api/admin/llm` → providers available? worker logs `LLM unavailable` | set a provider key; check `LLM_MODEL_*` strings |
| webhooks 401 | signing secret mismatch | same secret in LS dashboard and `.env` |
| disk filling up | scratch folders under the `jobs` volume | the hourly cleanup removes folders older than 2 days; `docker volume inspect videostudio_jobs` |

## Capacity (from the Phase 6 load test, see docs/PROGRESS.md)

A 13-second voice note at 1080×1920 draft takes about 25 s per job on one worker (transcribe 7 s, plan 3 s, render 10 s). Full-resolution
renders are roughly 4× slower in the render step. One worker container with `RENDER_WORKERS=2` handles ~1 job/minute; scale with
`WORKER_CONCURRENCY`.
