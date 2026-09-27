# VideoStudio SaaS — developer entry points. Everything runs in Docker.
WORKER_IMAGE ?= vs-worker:dev
WHISPER_MODEL ?= small
SHM ?= 1g
JOBS ?= $(PWD)/jobs

.PHONY: help worker-image test-worker smoke smoke-all e2e lint-worker

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
