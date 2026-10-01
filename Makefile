# VideoStudio SaaS — developer entry points. Everything runs in Docker.
WORKER_IMAGE ?= vs-worker:dev
WHISPER_MODEL ?= small
SHM ?= 1g
JOBS ?= $(PWD)/jobs

.PHONY: help worker-image test-worker smoke smoke-all e2e lint-worker plan-run providers up down logs build migrate seed test-api test-api-integration lint-api test web-dev test-web lint-web lighthouse

help:
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-16s %s\n", $$1, $$2}'

worker-image: ## build the worker image (WHISPER_MODEL=small|medium)
	docker build -f infra/docker/worker.Dockerfile --build-arg WHISPER_MODEL=$(WHISPER_MODEL) -t $(WORKER_IMAGE) .

test-worker: ## pytest apps/worker inside the worker image (mounts the source for fast iteration)
	docker run --rm --shm-size=$(SHM) -e WHISPER_MODEL=$(WHISPER_MODEL) \
	  -v "$(PWD)/apps/worker:/app/apps/worker" -v "$(PWD)/engine:/app/engine" $(WORKER_IMAGE) \
	  python -m pytest /app/apps/worker -q -x --timeout=1800 $(PYTEST_ARGS)

smoke: ## engine smoke test for a few templates at 9:16 + 16:9
	docker run --rm --shm-size=$(SHM) -e VT_OFFLINE=1 -v "$(PWD)/engine-dev/_smoke:/out" -v "$(PWD)/engine:/app/engine" $(WORKER_IMAGE) \
	  python3 /app/engine-dev/smoke.py steps quiz mirror top-five --sizes 9:16,16:9 --out /out

smoke-all: ## engine smoke test for all 24 templates at 9:16 + 16:9 (offline)
	docker run --rm --shm-size=$(SHM) -e VT_OFFLINE=1 -v "$(PWD)/engine-dev/_smoke:/out" -v "$(PWD)/engine:/app/engine" $(WORKER_IMAGE) \
	  python3 /app/engine-dev/smoke.py --sizes 9:16,16:9 --out /out

e2e: ## LLM-free end-to-end build (espeak → whisper → edit → plan → build --draft, watermark, 720p cap) into ./jobs/smoke
	docker run --rm --shm-size=$(SHM) -e VT_OFFLINE=1 -v "$(JOBS):/jobs" -v "$(PWD)/engine:/app/engine" -v "$(PWD)/engine-dev:/app/engine-dev" $(WORKER_IMAGE) \
	  python3 /app/engine-dev/e2e_build.py /jobs/smoke --draft --watermark /app/packages/shared/assets/watermark.png --max-height 720

lint-worker: ## ruff + mypy for apps/worker (inside the image)
	docker run --rm -v "$(PWD)/apps/worker:/app/apps/worker" $(WORKER_IMAGE) sh -c "cd /app/apps/worker && ruff check . && mypy vs_worker"

INPUT ?= jobs/voice.wav
TEMPLATE ?= steps
LANG ?= en
PLANNER ?= llm
LLM_ENV = -e ANTHROPIC_API_KEY -e OPENAI_API_KEY -e GEMINI_API_KEY -e OPENROUTER_API_KEY -e GROQ_API_KEY -e OLLAMA_BASE_URL \
  -e LLM_MODEL_PLANNER -e LLM_MODEL_FAST -e LLM_MODEL_VISION -e PLANNER_MODEL_FREE -e PLANNER_MODEL_PAID -e LLM_FALLBACK_CHAIN -e PLANNER_VISION_REVIEW

plan-run: ## run a job with the LLM planner: make plan-run INPUT=voice.m4a TEMPLATE=steps LANG=ar [PLANNER=llm|mock|fallback]
	docker run --rm --shm-size=$(SHM) $(LLM_ENV) -e WHISPER_MODEL=$(WHISPER_MODEL) -v "$(JOBS):/jobs" -v "$(abspath $(INPUT)):/input/$(notdir $(INPUT)):ro" $(WORKER_IMAGE) \
	  python -m vs_worker.cli run --input /input/$(notdir $(INPUT)) --template $(TEMPLATE) --lang $(LANG) --out /jobs --name manual --planner $(PLANNER) --draft

providers: ## show which LLM providers have credentials and the current routing
	docker run --rm $(LLM_ENV) $(WORKER_IMAGE) python -m vs_worker.cli providers

# ---- full stack -------------------------------------------------------------------------------------
COMPOSE ?= docker compose

up: ## build and start the whole stack (postgres, redis, minio, mailpit, api, worker)
	@test -f .env || cp .env.example .env
	$(COMPOSE) up -d --build
	@echo "API http://localhost:8000/docs · MinIO console http://localhost:9101 · Mailpit http://localhost:8025"

down: ## stop the stack (keeps volumes)
	$(COMPOSE) down

logs: ## follow api + worker logs
	$(COMPOSE) logs -f api worker

build: ## build api + worker images
	$(COMPOSE) build

migrate: ## run alembic migrations (api container)
	$(COMPOSE) run --rm --no-deps api alembic upgrade head

seed: ## create an admin-granted demo user (dev only)
	$(COMPOSE) run --rm --no-deps api python -m vs_api.seed

test-api: ## pytest apps/api against the compose test database (no worker needed)
	@test -f .env || cp .env.example .env
	$(COMPOSE) up -d postgres redis minio-init mailpit
	$(COMPOSE) run --rm --no-deps -e SKIP_MIGRATIONS=1 -e RATE_LIMITS_ENABLED=0 api \
	  python -m pytest /app/apps/api -q -m "not integration" --cov=vs_api --cov-report=term-missing $(PYTEST_ARGS)

test-api-integration: ## full flow with the worker (mock planner): register → upload → assets → preview → edit → swap → render → download
	@test -f .env || cp .env.example .env
	PLANNER_MODE=mock $(COMPOSE) up -d --build postgres redis minio-init mailpit api worker
	$(COMPOSE) run --rm --no-deps -e SKIP_MIGRATIONS=1 -e RATE_LIMITS_ENABLED=0 api python -m pytest /app/apps/api/tests/test_integration.py -q -m integration $(PYTEST_ARGS)

lint-api: ## ruff + mypy for apps/api
	$(COMPOSE) run --rm --no-deps -e SKIP_MIGRATIONS=1 api sh -c "cd /app/apps/api && ruff check . && mypy vs_api"

test: test-worker test-api ## everything that runs without a real LLM key

# ---- web ----------------------------------------------------------------------------------------------
web-dev: ## run the Next.js dev server on the host against the compose API (http://localhost:3000)
	cd apps/web && API_INTERNAL_URL=http://localhost:8000 npm run dev

lint-web: ## eslint + tsc for apps/web (host node)
	cd apps/web && npm run -s lint && npx tsc --noEmit

test-web: ## Playwright e2e + RTL/axe against the compose stack (mock planner); report in apps/web/playwright-report
	@test -f .env || cp .env.example .env
	PLANNER_MODE=mock S3_PUBLIC_ENDPOINT_URL=http://minio:9000 WEB_ORIGIN=http://web:3000 $(COMPOSE) up -d --build postgres redis minio-init mailpit api worker web
	PLANNER_MODE=mock S3_PUBLIC_ENDPOINT_URL=http://minio:9000 WEB_ORIGIN=http://web:3000 $(COMPOSE) --profile e2e run --rm --build e2e npx playwright test $(PW_ARGS)

lighthouse: ## Lighthouse accessibility ≥ 90 on landing + dashboard (inside the e2e image)
	PLANNER_MODE=mock S3_PUBLIC_ENDPOINT_URL=http://minio:9000 WEB_ORIGIN=http://web:3000 $(COMPOSE) --profile e2e run --rm e2e node e2e/lighthouse.mjs
