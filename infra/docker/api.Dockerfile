# API image: FastAPI + uvicorn; runs `alembic upgrade head` on start (entrypoint).
FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl tini postgresql-client \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY apps/api/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
COPY packages/shared /app/packages/shared
COPY engine /app/engine
COPY docs/previews /app/docs/previews
COPY apps/api /app/apps/api
RUN pip install --no-deps -e /app/apps/api && chmod +x /app/apps/api/entrypoint.sh
ENV VS_REPO_ROOT=/app
RUN useradd -m -u 10002 api && chown -R api:api /app
USER api
EXPOSE 8000
ENTRYPOINT ["/usr/bin/tini", "--", "/app/apps/api/entrypoint.sh"]
CMD ["uvicorn", "vs_api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
