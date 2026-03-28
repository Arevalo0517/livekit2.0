#!/usr/bin/env bash
set -euo pipefail

# Load environment variables (needed for POSTGRES_USER and POSTGRES_DB)
# shellcheck source=/opt/voiceai/.env
source /opt/voiceai/.env

BACKUP_DIR="/opt/voiceai/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/voiceai_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "=== Creating database backup ==="
docker compose -f /opt/voiceai/docker-compose.yml exec -T postgres \
  pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" | gzip > "$BACKUP_FILE"

# Restrict permissions so only the ubuntu user can read the backup
chmod 600 "$BACKUP_FILE"

echo "=== Backup saved to ${BACKUP_FILE} ==="

# Keep only last 7 days of local backups
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete

echo "=== Old backups cleaned up ==="
