#!/bin/sh
# Wait for Postgres, run migrations, then start the given command (uvicorn by default).
set -e
cd /app/apps/api
i=0
until python -c "import os, psycopg; psycopg.connect(os.environ['DATABASE_URL_SYNC'].replace('+psycopg', '')).close()" 2>/dev/null; do
  i=$((i+1)); [ $i -gt 60 ] && echo "postgres not reachable" && exit 1
  sleep 1
done
if [ "${SKIP_MIGRATIONS:-0}" != "1" ]; then
  alembic upgrade head
fi
exec "$@"
