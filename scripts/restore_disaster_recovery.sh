#!/usr/bin/env bash
# ==============================================================================
# RAGTUNE Enterprise - Disaster Recovery Restore Runner
# ==============================================================================
set -euo pipefail

POSTGRES_BACKUP_S3_PATH="${1:-}"
QDRANT_BACKUP_S3_PATH="${2:-}"

if [ -z "${POSTGRES_BACKUP_S3_PATH}" ] || [ -z "${QDRANT_BACKUP_S3_PATH}" ]; then
  echo "Usage: $0 <s3_path_to_postgres_backup> <s3_path_to_qdrant_snapshot>"
  echo "Example: $0 s3://ragtune-enterprise-storage/backups/postgres/ragtune_db_20260730.sql.gz s3://ragtune-enterprise-storage/backups/qdrant/snapshot.snapshot"
  exit 1
fi

RESTORE_TMP="/tmp/ragtune_dr_restore"
mkdir -p "${RESTORE_TMP}"

echo "====================================================================="
echo " RAGTUNE ENTERPRISE DISASTER RECOVERY RESTORE INITIATED"
echo "====================================================================="
echo "[1/4] Downloading PostgreSQL backup from ${POSTGRES_BACKUP_S3_PATH}..."
aws s3 cp "${POSTGRES_BACKUP_S3_PATH}" "${RESTORE_TMP}/postgres_backup.sql.gz"

echo "[2/4] Restoring PostgreSQL Relational Database..."
gunzip -c "${RESTORE_TMP}/postgres_backup.sql.gz" | PGPASSWORD="${POSTGRES_PASSWORD:-ragtune_secure_pass_2026}" psql \
  -h "${POSTGRES_HOST:-localhost}" \
  -U "${POSTGRES_USER:-ragtune_user}" \
  -d "${POSTGRES_DB:-ragtune_db}"

echo "[3/4] Downloading Qdrant Vector DB Snapshot from ${QDRANT_BACKUP_S3_PATH}..."
aws s3 cp "${QDRANT_BACKUP_S3_PATH}" "${RESTORE_TMP}/qdrant_snapshot.snapshot"

echo "[4/4] Restoring Qdrant Vector Collection..."
curl -s -X POST "http://${QDRANT_HOST:-localhost}:${QDRANT_PORT:-6333}/collections/ragtune_enterprise_documents/snapshots/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "snapshot=@${RESTORE_TMP}/qdrant_snapshot.snapshot"

rm -rf "${RESTORE_TMP}"

echo "====================================================================="
echo " DISASTER RECOVERY RESTORE COMPLETED SUCCESSFULLY"
echo "====================================================================="
