#!/usr/bin/env bash
# ==============================================================================
# RAGTUNE Enterprise - Automated PostgreSQL Backup & S3 Sync Script
# ==============================================================================
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/ragtune_backups/postgres"
BACKUP_FILE="${BACKUP_DIR}/ragtune_db_${TIMESTAMP}.sql.gz"
S3_BUCKET="${S3_BUCKET_NAME:-ragtune-enterprise-storage}/backups/postgres"
RETENTION_DAYS=30

mkdir -p "${BACKUP_DIR}"

echo "[INFO] Starting PostgreSQL Enterprise Backup at $(date)..."

# Perform compressed pg_dump
PGPASSWORD="${POSTGRES_PASSWORD:-ragtune_secure_pass_2026}" pg_dump \
  -h "${POSTGRES_HOST:-localhost}" \
  -U "${POSTGRES_USER:-ragtune_user}" \
  -d "${POSTGRES_DB:-ragtune_db}" \
  -F c -b -v \
  | gzip > "${BACKUP_FILE}"

echo "[INFO] Backup created successfully: ${BACKUP_FILE} ($(du -sh "${BACKUP_FILE}" | cut -f1))"

# Upload to S3 Object Storage with Server-Side Encryption
if command -v aws >/dev/null 2>&1; then
  echo "[INFO] Syncing backup file to S3: s3://${S3_BUCKET}/..."
  aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/$(basename "${BACKUP_FILE}")" --sse aws:kms
  echo "[INFO] S3 Backup Upload Complete."
fi

# Prune local backups older than 7 days
find "${BACKUP_DIR}" -type f -name "*.sql.gz" -mtime +7 -exec rm -f {} \;

echo "[SUCCESS] PostgreSQL Backup & Maintenance process finished."
