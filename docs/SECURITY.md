# Security review checklist (brief §5.10)

Each item names where it is enforced and how it was verified (test name or manual step). Re-run before every release.

| # | requirement | where | verified by |
|---|---|---|---|
| 1 | Uploads validated with ffprobe on the worker (real audio/video stream, duration ≤ limit), others rejected | `vt.py init` (`input_invalid`, `input_too_long`); `tasks.preview_job` marks the project failed (user error, no retry) | `test_engine_cli.py::test_init_duration_limit`, `test_init_rejects_non_media_file`; `test_pipeline.py::test_user_errors_are_not_transient` |
| 2 | Assets: real image/video content (Pillow / ffprobe), ≤ 40 MP, per-project count and size limits server-side, EXIF stripped | engine `media.py` (`asset_invalid`, `MAX_PIXELS`); API `assets.py` (415/413/422); worker marks `invalid` | `test_assets.py` (HEIC rotation + EXIF gone, bomb rejected), `test_projects.py::test_assets_presign_register_limits`, integration test (fake PNG → `invalid`) |
| 3 | Worker non-root, scratch dir per job deleted after `done`, `VT_OFFLINE=1` during render | `worker.Dockerfile` (`USER worker`), `tasks.render_job` (`rmtree`), `Pipeline(offline_render=True)` + socket guard | `test_engine_cli.py::test_offline_guard_fails_fast`; `docker compose exec worker id` → uid 10001 |
| 4 | Rate limits: auth 10/min/IP, project creation 10/h free · 60/h paid | `routers/auth.py` (slowapi), `ratelimit.check_user_limit` | `test_projects.py::test_project_rate_limit_per_user`; slowapi decorators on every auth route |
| 5 | Max concurrent jobs per user 1 free · 3 paid; priority queue for agency | `services.check_concurrency`, `render_options().priority` → queue `priority` | `test_projects.py::test_create_list_get_delete_and_concurrency` (429), `test_billing_lemonsqueezy.py::test_plan_gating_render_options` |
| 6 | Presigned URLs ≤ 15 min; content type and size enforced by the presign policy | `storage.presign_upload` (POST policy: `Content-Type`, `content-length-range`), `presign_ttl_s=900` | `test_projects.py::test_presign_rejects_bad_types_and_sizes`; policy fields visible in `PresignOut` |
| 7 | CORS locked to the web origin; secure httpOnly cookies; CSRF token for cookie-auth POSTs | `main.py` CORS (`WEB_ORIGIN`), `routers/auth.py` cookies (`httponly`, `secure` in prod, `SameSite=Lax`), `deps.py` double submit | `test_auth.py::test_register_login_me_and_cookies` (403 `csrf` without the header) |
| 8 | LLM outputs treated as untrusted (validated JSON, HTML-escaped by the engine) | `planner/schema.py` (Pydantic + whitelist + anchors + asset names); engine `VT.esc()` | `test_schema.py`, `test_llm_planner.py` (bad anchor / unknown scene / unknown asset rejected) |
| 9 | Secrets never in the repo; documented in `.env.example` / `docs/CREDENTIALS.md` | `.gitignore` | `git ls-files | grep -c '^.env$'` → 0 |
| 10 | Webhooks verified (HMAC) and processed exactly once | `payments.LemonSqueezyProvider.verify`, `record_and_apply` | `test_billing_lemonsqueezy.py` (401 on bad signature, duplicates) |
| 11 | Admin endpoints need `X-Admin-Key`; never exposed to the browser | `deps.require_admin` | `test_catalog_billing_admin.py::test_admin_endpoints` (401 without key) |
| 12 | Email verification enforced in prod for creating projects / rendering | `deps.verified_user` (`APP_ENV=prod`) | code path; dev/test skip it on purpose |
| 13 | No secrets, tokens or full transcripts at INFO level | request logs carry path/status/ids only; transcripts are never logged | `grep -rn "transcript" apps/api/vs_api | grep -i log` → none |
| 14 | Network timeouts and retries on every outbound call | LiteLLM (`timeout`, `num_retries`), fonts (`retries=3`), TTS, email, Lemon Squeezy (`timeout=20`), S3 (botocore defaults) | code review |
| 15 | Security headers at the edge (HSTS, nosniff, frame deny, referrer policy), TLS only | `infra/caddy/Caddyfile`, Next `headers()` | `curl -I https://<domain>` after deploy |
| 16 | Resource limits and restart policies in prod | `docker-compose.prod.yml` | `docker stats` |

## Known gaps (tracked in docs/PROGRESS.md)

- No per-IP limit on the webhook endpoint (the signature check is the gate); add a Caddy rate limit if abuse appears.
- Google OAuth is not implemented (flag off).
- Legal pages are placeholders until the owner provides the texts.
