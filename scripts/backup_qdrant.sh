#!/usr/bin/env bash
# ==============================================================================
# RAGTUNE Enterprise - Qdrant Vector DB Snapshot & S3 Sync Script
# ==============================================================================
set -euo pipefail

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
QDRANT_HOST="${QDRANT_HOST:-localhost}"
QDRANT_PORT="${QDRANT_PORT:-6333}"
COLLECTION_NAME="${COLLECTION_NAME:-ragtune_enterprise_documents}"
BACKUP_DIR="/tmp/ragtune_backups/qdrant"
S3_BUCKET="${S3_BUCKET_NAME:-ragtune-enterprise-storage}/backups/qdrant"

mkdir -p "${BACKUP_DIR}"

echo "[INFO] Triggering Qdrant Vector Collection Snapshot for '${COLLECTION_NAME}'..."

# Trigger snapshot creation via REST API
SNAPSHOT_RESP=$(curl -s -X POST "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${COLLECTION_NAME}/snapshots")
SNAPSHOT_NAME=$(echo "${SNAPSHOT_RESP}" | grep -o '"name":"[^"]*' | cut -d'"' -f4 || true)

if [ -z "${SNAPSHOT_NAME}" ]; then
  echo "[WARNING] Primary collection snapshot failed or collection empty. Attempting cluster full snapshot..."
  SNAPSHOT_RESP=$(curl -s -X POST "http://${QDRANT_HOST}:${QDRANT_PORT}/snapshots")
  SNAPSHOT_NAME=$(echo "${SNAPSHOT_RESP}" | grep -o '"name":"[^"]*' | cut -d'"' -f4 || true)
fi

echo "[INFO] Created Qdrant Snapshot: ${SNAPSHOT_NAME}"

# Download snapshot archive
LOCAL_SNAPSHOT_FILE="${BACKUP_DIR}/qdrant_${COLLECTION_NAME}_${TIMESTAMP}.snapshot"
curl -s -o "${LOCAL_SNAPSHOT_FILE}" "http://${QDRANT_HOST}:${QDRANT_PORT}/collections/${COLLECTION_NAME}/snapshots/${SNAPSHOT_NAME}"

echo "[INFO] Qdrant Snapshot downloaded: ${LOCAL_SNAPSHOT_FILE}"

# Sync to S3 storage
if command -v aws >/dev/null 2>&1; then
  echo "[INFO] Uploading vector snapshot to S3: s3://${S3_BUCKET}/..."
  aws s3 cp "${LOCAL_SNAPSHOT_FILE}" "s3://${S3_BUCKET}/$(basename "${LOCAL_SNAPSHOT_FILE}")" --sse aws:kms
  echo "[INFO] Qdrant Snapshot S3 Upload Complete."
fi

echo "[SUCCESS] Qdrant Vector DB backup process finished."
