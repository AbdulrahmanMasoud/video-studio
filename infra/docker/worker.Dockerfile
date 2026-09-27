# Worker image: runs the Video Studio engine CLI (vt.py) and, later, the RQ worker.
# Phase 0: throwaway build used to verify the engine inside Docker.
ARG WHISPER_MODEL=small
FROM python:3.12-slim-bookworm AS base
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    VT_CACHE=/cache/video-studio HF_HOME=/cache/huggingface
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg espeak-ng ca-certificates curl tini fonts-noto-core \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY engine/video-engine/scripts/requirements.txt /tmp/engine-requirements.txt
RUN pip install -r /tmp/engine-requirements.txt \
    && python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*
# Bake the whisper model into the image (small for tests, medium for prod).
ARG WHISPER_MODEL
RUN python -c "from faster_whisper import WhisperModel; WhisperModel('${WHISPER_MODEL}', device='cpu', compute_type='int8')" \
    && echo "whisper ${WHISPER_MODEL} cached"
COPY engine /app/engine
COPY engine-dev /app/engine-dev
# non-root user; cache dirs writable
RUN useradd -m -u 10001 worker && mkdir -p /cache /jobs && chown -R worker:worker /cache /jobs /app /ms-playwright
USER worker
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python3", "/app/engine/video-engine/scripts/vt.py", "doctor"]
