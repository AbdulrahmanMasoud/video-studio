#!/bin/sh
# Nightly pg_dump → S3 (outputs bucket, prefix backups/). Runs in the `backup` service; keeps 14 days.
set -eu
: "${POSTGRES_USER:=videostudio}" "${POSTGRES_PASSWORD:=videostudio}" "${POSTGRES_DB:=videostudio}"
: "${S3_ENDPOINT_URL:?}" "${S3_BUCKET:?}" "${S3_ACCESS_KEY:?}" "${S3_SECRET_KEY:?}" "${S3_REGION:=us-east-1}"
: "${BACKUP_HOUR_UTC:=03}" "${BACKUP_KEEP_DAYS:=14}"
if ! command -v aws >/dev/null 2>&1; then
  apt-get update -qq >/dev/null && apt-get install -y -qq curl unzip >/dev/null \
    && curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip" -o /tmp/awscli.zip && cd /tmp && unzip -q awscli.zip && ./aws/install >/dev/null && cd /
fi
export AWS_ACCESS_KEY_ID="$S3_ACCESS_KEY" AWS_SECRET_ACCESS_KEY="$S3_SECRET_KEY" AWS_DEFAULT_REGION="$S3_REGION" PGPASSWORD="$POSTGRES_PASSWORD"
backup() {
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  file="/tmp/videostudio-$stamp.sql.gz"
  pg_dump -h postgres -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip -9 > "$file"
  aws --endpoint-url "$S3_ENDPOINT_URL" s3 cp "$file" "s3://$S3_BUCKET/backups/$(basename "$file")" --only-show-errors
  rm -f "$file"
  echo "backup $stamp uploaded"
  cutoff=$(date -u -d "-${BACKUP_KEEP_DAYS} days" +%Y%m%d 2>/dev/null || date -u -v-"${BACKUP_KEEP_DAYS}"d +%Y%m%d)
  aws --endpoint-url "$S3_ENDPOINT_URL" s3 ls "s3://$S3_BUCKET/backups/" | awk '{print $4}' | while read -r name; do
    d=$(echo "$name" | sed -E 's/videostudio-([0-9]{8}).*/\1/')
    if [ -n "$d" ] && [ "$d" -lt "$cutoff" ]; then aws --endpoint-url "$S3_ENDPOINT_URL" s3 rm "s3://$S3_BUCKET/backups/$name" --only-show-errors; fi
  done
}
if [ "${1:-}" = "once" ]; then backup; exit 0; fi
echo "backup service: daily at ${BACKUP_HOUR_UTC}:00 UTC, keeping ${BACKUP_KEEP_DAYS} days"
while true; do
  if [ "$(date -u +%H)" = "$BACKUP_HOUR_UTC" ]; then backup; sleep 3600; fi
  sleep 300
done
