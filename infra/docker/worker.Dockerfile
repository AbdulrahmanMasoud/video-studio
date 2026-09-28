# Worker image: the Video Studio engine CLI (vt.py) + the RQ worker package (apps/worker).
#   docker build -f infra/docker/worker.Dockerfile --build-arg WHISPER_MODEL=medium -t vs-worker .
# Build args: WHISPER_MODEL (small for tests/CI, medium for prod), INSTALL_DEV (1 = pytest/ruff/mypy),
#             FONT_SCRIPTS (comma list of script keys to pre-cache; empty = all).
ARG PYTHON_IMAGE=python:3.12-slim-bookworm
FROM ${PYTHON_IMAGE} AS base
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    VT_CACHE=/cache/video-studio HF_HOME=/cache/huggingface
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg espeak-ng ca-certificates curl tini fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# 1) pre-cache Google Fonts for every script/role so rendering works with VT_OFFLINE=1 (stdlib only, so it runs
#    before pip: only fonts.py/common.py are copied here and the slow network-bound layer survives dependency changes).
ARG FONT_SCRIPTS=
COPY engine/video-engine/scripts/vtlib/common.py engine/video-engine/scripts/vtlib/fonts.py /tmp/vtlib/vtlib/
RUN touch /tmp/vtlib/vtlib/__init__.py \
    && cd /tmp/vtlib && FS="${FONT_SCRIPTS}" python3 -c "from vtlib.fonts import precache; import os, sys; s=os.environ.get('FS') or None; r=precache(s.split(',') if s else None); sys.exit(0 if all(r.values()) else 'font cache incomplete: ' + str([k for k,v in r.items() if not v]))" \
    && du -sh /cache/video-studio/fonts && rm -rf /tmp/vtlib

# 2) pinned Python deps (engine + worker; compiled with `uv pip compile`), then Playwright's Chromium
COPY apps/worker/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt \
    && python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

# 3) bake the whisper model
ARG WHISPER_MODEL=small
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('${WHISPER_MODEL}', device='cpu', compute_type='int8')" \
    && echo "whisper ${WHISPER_MODEL} cached"
ENV WHISPER_MODEL=${WHISPER_MODEL}

# 4) engine + dev tools
COPY engine /app/engine
COPY engine-dev /app/engine-dev

# 5) worker package
COPY apps/worker /app/apps/worker
COPY packages/shared /app/packages/shared
RUN pip install --no-deps -e /app/apps/worker

# runtime: non-root, offline by default for the Hub, network guard is set per step by the pipeline
ENV HF_HUB_OFFLINE=1 PYTHONPATH=/app/engine/video-engine/scripts
RUN useradd -m -u 10001 worker && mkdir -p /cache /jobs && chown -R worker:worker /cache /jobs /app /ms-playwright
USER worker
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python3", "/app/engine/video-engine/scripts/vt.py", "doctor"]
