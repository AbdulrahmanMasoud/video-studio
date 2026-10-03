# Progress

## Phase 0 — Understand and verify the engine — DONE (2026-09-27)

### What was done
- Unzipped `video-studio.zip`; `plugins/video-studio/skills` → `engine/` (verbatim, plus the upstream
  `LICENSE`), `dev/` → `engine-dev/`, `docs/previews` → `docs/previews`.
- Fixed skill paths in `engine-dev/smoke.py`, `mkplan.py`, `gen_skills.py` (`SK = ROOT / "engine"`,
  smoke output in `engine-dev/_smoke/`) and in `references/template-authoring.md`.
- Read `vt.py`, all of `vtlib/`, `runtime/engine.js`, `video-engine/SKILL.md`, all `references/*.md`,
  `steps/SKILL.md`, `mirror/SKILL.md`, every `template.json`.
- Wrote `docs/ARCHITECTURE.md` (§5 diagram, service table, pipeline mapping, verified engine facts) and
  `docs/DECISIONS.md`.
- `infra/docker/worker.Dockerfile`: python 3.12-slim + ffmpeg + Playwright Chromium + faster-whisper
  with the model baked in (`WHISPER_MODEL` build arg) + espeak-ng + tini, non-root. Image: 3.7 GB.
- `engine-dev/e2e_build.py`: LLM-free end-to-end check (espeak-ng voice → transcribe → analyze → edit →
  simple `steps` plan anchored to real word indices → stills → build).

### What was tested (inside the Docker image, `vs-worker:phase0`)
| check | command | result |
|---|---|---|
| dependencies | `vt.py doctor` | `ALL GOOD` (numpy, scipy, soundfile, PIL, playwright, faster_whisper, ffmpeg, ffprobe, headless chromium) |
| catalog | `vt.py templates` | 24 templates listed |
| intake guard | `vt.py init JOB --template steps` (no lang/size) | exit 2 with the documented error |
| stills smoke | `smoke.py steps quiz --sizes 9:16,16:9` | `ok` ×4, `FAILED: none`; contact sheets inspected |
| full build | `e2e_build.py /jobs/smoke --draft` | 33 words transcribed (`small`), edit 13.7 s → 13.1 s, 5 stills, 393 frames rendered, 15 SFX cues, lofi music, mix −14.0 LUFS / TP −1.1 dBTP, `final.mp4` h264+aac 540×960, QA report written |

### Findings to carry into Phase 1
1. `build --draft` renders at half resolution and QA then reports `resolution 540x960 != requested
   1080x1920`. Expected for drafts; the worker must treat this issue as informational in draft mode
   (or QA should know the render scale).
2. Fonts are fetched from Google Fonts at render time; the image has no font cache, so an offline
   render silently falls back to system fonts. Phase 1 pre-caches all script/role combinations at
   build time and adds `VT_OFFLINE=1`.
3. `[vt]` log lines are plain text; Phase 1 adds `--json`.
4. Whisper `small` on espeak-ng speech yields clean word timings (33/33 words kept), good enough for
   fixtures.
5. `engine.js` does not fail on an unknown media name (draws a placeholder), so asset-name validation
   must live in the planner.
6. The first `transcribe` in a fresh container spends ~1 s on a HF Hub metadata request even with the
   model baked in; set `HF_HUB_OFFLINE=1` in the worker image (Phase 1).

### Open questions for the owner
1. **Repo root**: the monorepo is this repository root (not a nested `video-saas/`). OK?
2. **Whisper in prod**: `medium` int8 on CPU is slow for 10-minute inputs (roughly real time or slower
   on 2 vCPU). Do you want GPU workers as an option, or is CPU with a 15-minute timeout acceptable?
3. **Arabic sample**: please provide one Arabic recording (voice note, 30–90 s) for the Phase 2
   manual planner run.
4. **LLM keys**: which provider keys will exist in dev? (Anthropic is the default; others are only
   smoke-tested when a key is present.)
5. **Draft quality for previews**: should the user-facing preview be stills only (fast, current design)
   or also a low-res draft MP4 (costs a render)?

## Phase 1 — Engine productisation — DONE (2026-09-27)

### What was done
Engine (`engine/video-engine`, CLI stays backward compatible; details in `CHANGELOG.md`):
- edge-tts removed → `TTSProvider` (`openai`, `espeak` for tests; default `none`). `vt.py tts` writes `tts.mp3`, timings come from `transcribe`.
- `mux`/`build`: `--watermark PNG --watermark-pos --watermark-opacity --watermark-scale`, `--max-height` (short-side cap). QA now checks the *delivered* size.
- `init --duration-limit`, non-media inputs rejected, typed `error_code`s (`intake_missing`, `input_too_long`, `input_invalid`, `asset_invalid`, `tts_*`).
- `--json` / `VT_JSON=1` structured logs with `progress` events; `VT_OFFLINE=1` socket guard (loopback only) + `HF_HUB_OFFLINE`.
- `fonts --precache`: 92 Google Fonts families for 29 scripts × 7 roles baked into the image (78 MB), parallel downloads with retries.
- Assets: HEIC/HEIF/AVIF/WebP via pillow-heif, EXIF rotation applied + metadata stripped, alpha kept (PNG, `--fit contain`), 40 MP guard,
  clip `--start/--duration/--max-duration`, audio dropped unless `--keep-audio` (mixed at the scene), `vt.py assets --manifest` → `media/index.json`.
- SIGTERM/SIGINT handler terminates ffmpeg/Chromium children and exits 143/130; `run()` has a timeout.
- Mix true-peak ceiling −1.5 dBTP (was −1.2) so AAC output stays under −1 dBTP.

Worker (`apps/worker`, package `vs_worker`):
- `Pipeline(spec, workdir)`: `prepare_preview()` (init → tts? → transcribe → analyze/edit → cam media → assets → plan → stills),
  `apply_plan()` (re-validate with stills), `render()` (render → sfx → music → mix → mux → qa), `cleanup()`; step events, per-step timeouts,
  `PipelineError(code, transient, user_error)`.
- `EngineRunner`: JSON-event subprocess driver, process-group kill on timeout.
- Deterministic fallback planner (`steps`, `mirror`, generic `text` for the other 22) with sentence/pause sectioning, 4–6-word titles,
  announced-count detection (en/ar), en/ar labels.
- Offline fixtures: espeak-ng voice (3 sentences), testsrc2 screen recording / talking-head stand-in, HEIC with EXIF orientation, transparent PNG, 90 s clip.
- Pinned deps via `uv pip compile` (`apps/worker/requirements.txt`), `Makefile`, GitHub Actions `ci.yml` (build image → doctor → ruff/mypy → smoke all → pytest).

### What was tested (image `vs-worker:phase1`, whisper `small`)
| check | command | result |
|---|---|---|
| lint | `ruff check . && mypy vs_worker` (in image) | clean |
| unit + CLI + assets + mux + TTS + planner | `pytest apps/worker -m "not slow"` | 36 passed, 1 skipped (OpenAI TTS: no key) |
| **DoD pipeline** | `pytest apps/worker/tests/test_pipeline.py` | 5 passed: espeak fixture → transcribe (`small`, autodetect `en`) → edit → fallback plan → stills → render `--draft` → mux with watermark + `--max-height 720` → MP4 exists, has audio, −14.0 LUFS (±2 LU asserted), TP −1.2, no QA issues; video-input `mirror` job registers `cam`; `apply_plan` rejects bad anchor / unknown scene with `plan_invalid`; user errors non-transient; TTS script job |
| full suite | `pytest apps/worker` | 41 passed, 1 skipped in 93 s |
| engine smoke | `smoke.py --sizes 9:16,16:9` with `VT_OFFLINE=1` | 48/48 ok (24 templates × 2 sizes), no browser errors |
| SIGTERM | `test_sigterm_stops_cli_cleanly` | exit 143, children gone |

### Findings / open items
1. Google Fonts occasionally refuses a few subset files under parallel load (12/119 for one CJK family before retries were added);
   the build now retries 3× with backoff. If a family still misses files, the render falls back per glyph range: watch the build log line `failed to download`.
2. HEIC decoding relies on pillow-heif (libheif/libde265, LGPL) → license/patent question for the owner (DECISIONS #9).
3. `--keep-audio` clip audio is mixed at −6 dB under the voice for the scene length only; there is no per-clip gain control yet.
4. The fallback planner ignores the brief except `title`; brand palette/fonts are applied by the engine from `init`.
5. Next (Phase 2): LLM planner with the validation loop, editable fields, asset slots, edit-decision step, MockLLM; the `Planner` protocol in `pipeline.py` is the plug-in point.

## Phase 2 — LLM planner — DONE (2026-09-27), pending the owner's real-model run

### What was done (`apps/worker/vs_worker/llm/`, `planner/`)
- `LLMClient` (LiteLLM) with JSON mode / JSON-only + repair, vision input, fallback chain, timeouts, cost accounting (LiteLLM map → `plans.yaml`).
- `LLMSettings`: per-task routing with env defaults (first provider with a key wins: Anthropic → OpenAI → Ollama), `app_settings` overrides,
  free/paid tier models, `provider_status()` for `/admin/llm`.
- `LLMPlanner`: prompt builder (role, template SKILL.md, plan schema, hard rules, asset rules, brief, assets, shortened example — Arabic when
  the video is Arabic —, indexed transcript), validation loop (Pydantic + whitelist + anchors + asset names → engine stills), ≤ 3 attempts →
  `plan_failed`, fallback planner when the LLM is unreachable, optional vision review, `editable_fields`, `asset_slots`, `unused_assets`,
  usage/cost on the job (`llm.*` in job.json, `PreviewResult.llm`).
- Edit-decision step (fast model → validated `--drop` ranges) and asset auto-description (vision) wired into the pipeline.
- `Pipeline.apply_texts()` / `apply_assets()` (swap, remove, insert a full-frame `media` scene at a word, interrupted scene resumes).
- `MockLLM` (example plan re-anchored to the transcript, media slots filled, scripted queue) and `python -m vs_worker.cli`.
- `packages/shared/plans.yaml` (plans, limits, basic templates, LLM price table).

### What was tested (image `vs-worker:phase2`)
| check | result |
|---|---|
| `ruff` + `mypy` | clean (21 source files) |
| `pytest apps/worker` (full) | 80 passed, 7 skipped (6 real-provider smokes without keys, 1 OpenAI TTS) in 101 s |
| DoD: valid plan accepted | `test_mock_plan_accepted_and_usage_recorded` |
| DoD: bad word index repaired within 3 attempts (mock: bad then good) | `test_bad_anchor_repaired_within_attempts`, engine errors loop: `test_engine_errors_feed_the_repair_loop` |
| DoD: unknown scene type / unknown asset rejected | `test_unknown_scene_type_and_asset_rejected_then_plan_failed` (→ `plan_failed` after 3) |
| DoD: editable fields + asset slots round-trip | `test_apply_text_edits_roundtrip…`, `test_asset_slots_and_swap_remove_insert`, engine-backed `test_top_five_places_each_image_in_its_rank` (edit → swap → remove → insert → stills) |
| DoD: top-five with 5 Pillow images placed in ranks, contact sheet shows them | same test: ≥ 20 % of each rank still's pixels are the asset colour |
| every provider through the same code path | `test_every_provider_same_code_path[6 providers]` (fake transport; Ollama `api_base`, JSON mode flag) |
| edit decisions | `test_edit_decision_validation`, pipeline `test_mock_planner_full_pipeline_with_llm_edit_decision` (2 words dropped end to end) |
| Arabic example / RTL plan | `test_arabic_example_plan_is_used_for_arabic` (quiz, labels in Arabic, stills render) |
| engine smoke after the `edit.py` change | 48/48 ok |

### Not done / needs the owner
1. **Manual run with a real model** (DoD): no provider key is available in this environment. Run
   `docker run --rm -e ANTHROPIC_API_KEY -v $PWD/jobs:/jobs vs-worker:dev python -m vs_worker.cli run --input /jobs/voice.m4a --template steps --lang ar --size 9:16 --out /jobs`
   on the espeak fixture and on your Arabic sample and share `qa/contact_sheet.jpg` + `plan.json`. `tests/test_llm_real.py` also runs per key.
2. Vision review is off by default (`PLANNER_VISION_REVIEW=1` to enable); cost is one extra vision call per plan.
3. The fallback chain is empty by default; set `LLM_FALLBACK_CHAIN` (e.g. `openai/gpt-4o,groq/llama-3.3-70b-versatile`).

## Phase 3 — API and database — DONE (2026-09-28)

### What was done
- `docker-compose.yml`: postgres (+ test database init), redis, minio (+ bucket init container), mailpit, api, worker (`jobs` volume,
  `shm_size 1g`, `WORKER_CONCURRENCY` replicas). `.env.example` is enough for `make up`.
- `apps/api` (FastAPI, SQLAlchemy 2 async, Alembic, RQ, boto3): every endpoint of §5.6 except the Lemon Squeezy specifics (Phase 5) and
  Google OAuth (flag off). Migration `0001_initial` creates the §5.7 schema and seeds the 6 launch templates.
- Worker RQ tasks (`preview_job`, `render_job`, `edit_job`) with status/progress/events, credits reserve → commit/release, S3 in/out, emails.
- Rate limits (auth 10/min/IP, projects 10/h free · 60/h paid), concurrency (1 free · 3 paid), priority queue for agency, presign policies,
  CORS, httpOnly cookies + CSRF, `/health`, `/metrics`, JSON logs with request ids.

### What was tested
| check | result |
|---|---|
| `ruff` + `mypy` (api, worker) | clean |
| `pytest apps/api -m "not integration"` (in-process app, real Postgres/Redis/MinIO/Mailpit) | 19 passed; coverage 93 % total — routers: auth 93, me 98, templates 100, uploads 100, projects 96, assets 93, template-requests 94, billing 92, admin 94, health 76; services 98 |
| email flows | verification and reset tokens read back from Mailpit's API |
| credits | reserve at render, 402 when short, release on failure, retry re-reserves, ledger == fast path |
| **DoD integration** (`test_integration.py`, live api + worker with `PLANNER_MODE=mock`) | register → upload the espeak MP3 → top-five project with 3 PNG assets + 1 invalid → `preview_ready` in ~8 s (assets ready/invalid, AI descriptions, all 3 placed) → edit a text → swap an asset → render → `done` → download a valid MP4 (h264 + aac, 720p, 1 credit committed) — 32 s end to end |
| asset limits / invalid file | 415 for bad types, 413 over size, 422 over 20 per project, `invalid` status for a fake PNG |
| `pytest apps/worker -m "not slow"` after the shared-core refactor | passing |
| `make up` after `docker compose down -v` | all services healthy in ~10 s, health `ok`, integration flow passes on the fresh stack |

### Findings
1. Chromium crashed ("Target crashed") on the first containerised full-resolution render: 4 parallel pages at 1080×1920 in a 6.5 GB Docker
   VM. Fixed with `--disable-dev-shm-usage --no-zygote` and `RENDER_WORKERS=2`; per-page memory is roughly 600 MB at 1080p.
2. Coverage was misleading (51 % on tested routers) until greenlet concurrency was enabled (DECISIONS #33).
3. Port 9000 was taken on the owner's machine; MinIO now uses 9100/9101.
4. Lemon Squeezy checkout/portal/webhooks return 501 until Phase 5; the mock provider (`POST /billing/mock/subscribe`) works.

## Phase 4 — Web app — DONE (2026-10-01)

### What was done (`apps/web`)
- Next.js 15 (App Router, TypeScript, Tailwind 4) with next-intl: `/en` and `/ar` routes, `dir="rtl"` for Arabic, logical utilities,
  Inter + IBM Plex Sans Arabic, a locale switcher that keeps the current page, full `en.json`/`ar.json` catalogs (key parity checked).
- Pages: landing (hero, how it works, 24-template gallery), pricing, terms/privacy/refunds placeholders, login, register, forgot, reset,
  verify, dashboard, new-video wizard (5 steps), project page, billing (plans + mock checkout), settings (locale, brand kit, delete account).
- Direct-to-S3 uploads with progress (presigned POST), client-side duration check, SSE status with always-on polling fallback,
  contact-sheet preview, edit-texts form, asset panel (slots, swap, remove, insert at a word, unused list, invalid files), render with
  credit cost, download, retry, typed error messages, verify-email banner, request-a-template dialog.
- Same-origin `/api/*` rewrite to the API (first-party cookies + CSRF header); client types generated from the OpenAPI document.
- `infra/docker/web.Dockerfile` (standalone), `infra/docker/e2e.Dockerfile` (Playwright 1.63 + Lighthouse), compose `web` + `e2e` profile,
  `make web-dev / lint-web / test-web / lighthouse`, CI `web` job.

### What was tested
| check | result |
|---|---|
| `tsc --noEmit`, `eslint` | clean |
| `next build` | all routes compile (standalone output) |
| Playwright e2e `flow.spec.ts` (register → wizard: upload the MP3, language/size, top-five, 2 generated PNG assets, brief → preview → edit a text → swap an asset → render → download) | passed, 42 s end to end against the compose stack with the mock planner |
| Playwright `rtl.spec.ts` (Arabic landing, register, dashboard at 390 px and 1280 px: `dir=rtl`, no horizontal overflow, screenshots, axe WCAG 2.0/2.1 A+AA no serious/critical) | 3 passed |
| axe on the English landing | passed |
| Lighthouse accessibility (`e2e/lighthouse.mjs`) | landing 100, dashboard 100 |
| API unit suite after the typed `/me` and `/templates` schemas | passing |

### Findings
1. Compose `env_file` reads an inline comment after an empty value as the value (`LLM_MODEL_PLANNER=   # default…` became the model name).
   Comments in `.env.example` now sit on their own lines. Worth remembering for every future key.
2. The SSE stream through the Next.js rewrite is not guaranteed to flush, so the project page polls every 2.5 s while a job runs and uses SSE only
   as an accelerator (DECISIONS #36).
3. The Playwright browser crashed ("Page crashed") during the worker's render because the container's /dev/shm is 64 MB; the e2e service now has
   `shm_size: 1g` and launches Chromium with `--disable-dev-shm-usage`.
4. `S3_PUBLIC_ENDPOINT_URL` and `WEB_ORIGIN` are shell-overridable in compose for the in-network e2e run (`make test-web` sets them); on a laptop
   the defaults (localhost:9100 / localhost:3000) are right for a real browser.
5. Google OAuth stays behind its flag (not built); the "paste a script" source is disabled in the UI until `TTS_ENABLED=1` with a provider.

## Phase 5 — Billing, plans, limits — DONE (2026-10-03)

### What was done
- Lemon Squeezy provider (checkout URL via API, portal link, HMAC webhook verification), mock provider, normalised billing events applied
  exactly once; subscription lifecycle, renewals, refunds, payment-failed email; `GET /billing/subscription`, `GET /admin/webhooks`.
- Plan gating verified end to end (watermark + 720p on free, none on paid; template tiers; concurrency 1/3; priority queue for agency).
- Hourly cleanup job (inputs 7 days, outputs 30/180 days, stale assets, scratch folders) scheduled by the worker at start.
- Web: billing page with subscription status/portal/checkout confirmation; dark cinematic redesign of the marketing site and app theme.
- `docs/CREDENTIALS.md` (all keys + Lemon Squeezy setup).

### What was tested
| check | result |
|---|---|
| `pytest apps/api` (26 tests, incl. `test_billing_lemonsqueezy.py`) | passing, coverage 92 % (`payments.py` 83 %, `billing.py` 89 %) |
| recorded webhook payloads: created → payment_success (credits 2 → 50) → duplicate (no change) → updated (variant → agency) → cancelled (flag, plan kept) → payment_failed (email) → expired (free, credits 2) | asserted |
| order_refunded after a paid month: credits 50 → 0, plan free, duplicate ignored; bad / missing signature → 401 | asserted |
| credits under concurrent renders (2 threads, 1 credit, `FOR UPDATE`) | exactly one reservation; release restores the balance |
| free vs paid render options (watermark / 720 vs none / 2160, priority) | asserted |
| cleanup job in the running worker | runs, re-schedules itself (`cleanup-hourly` → scheduled) |
| web after the redesign: lint/typecheck/build, Playwright flow + Arabic RTL (3 pages) + axe, Lighthouse | all passing; accessibility 100 / 100 (muted text token raised to 7:1 contrast) |

## Phase 6 — Hardening and production — DONE (2026-10-03) · **MVP complete**

### What was done
- `docker-compose.prod.yml` + `infra/caddy/Caddyfile`: TLS (Let's Encrypt), security headers, `/api/*` → api, `/` → web; MinIO/Mailpit on a
  dev-only profile; restart policies; CPU/memory limits; `backup` sidecar (nightly `pg_dump` → S3, 14 days; `make backup-now`).
- Sentry (optional, DSN-gated) in api, worker and web; `/metrics` and `/health` already from Phase 3.
- `infra/scripts/loadtest.py` + `RENDER_DRAFT` + `RATE_LIMITS_ENABLED` compose overrides; `make loadtest`.
- `docs/RUNBOOK.md` (fresh-VM deploy, day-2 ops, backups/restore, key rotation, incidents, capacity), `docs/SECURITY.md` (§5.10 checklist
  with the verifying test per item), `docs/CREDENTIALS.md`, README deploy section; CI validates the prod compose config.
- Legal pages are placeholders (owner provides the texts).

### What was tested
| check | result |
|---|---|
| `docker compose -f docker-compose.yml -f docker-compose.prod.yml config` | valid (api, backup, caddy, postgres, redis, web, worker) |
| full rebuild of api, worker, web, e2e images from the current tree | ok (web lockfile regenerated with the image's npm) |
| `pytest apps/api` | 26 passed, 92 % coverage |
| `pytest apps/worker -m "not slow"` | 72 passed, 7 skipped (keys) |
| Playwright (flow + RTL + axe) and Lighthouse on the redesigned site | 5 passed; landing 100, dashboard 100 |
| API integration flow (live api + worker) | passed |
| **load test**: 10 concurrent jobs, draft renders, mock planner, 1 worker (`RENDER_WORKERS=2`), 6.5 GB Docker VM | 10/10 done in 234 s wall → **2.6 jobs/min per worker**; preview p50 27 s, render p50 123 s, total p50 150 s, max 234 s. Full-resolution renders are ≈4× slower in the render step → plan ≈0.7 jobs/min per worker at 1080p; scale with `WORKER_CONCURRENCY`. |

### Known limitations (MVP)
1. The owner's real-LLM manual run (Phase 2 DoD) has not been done here: no provider key in this environment. With a key, `make plan-run` or
   any project in the UI exercises it.
2. Google OAuth is behind its flag and not implemented.
3. The "paste a script" source needs `TTS_ENABLED=1` and an OpenAI key; it is hidden in the UI otherwise.
4. Lemon Squeezy is wired and tested against recorded payloads; a live checkout has to be verified once with real test-mode keys
   (`docs/CREDENTIALS.md`, "Send test event").
5. Legal pages are placeholders. Outputs in object storage are not backed up (rely on bucket versioning).
6. The fallback planner's storyboards are intentionally plain; quality comes from the LLM planner.
7. Whisper `medium` on CPU is roughly real time; a GPU worker would need a separate image (not built).

## Phase 7 — Mixed templates — not started (post-MVP, waits for the owner's "MVP complete")
