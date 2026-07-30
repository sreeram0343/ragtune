# RAGTUNE Enterprise - Operational Runbooks & Incident Response

This document provides step-by-step operational runbooks for SRE, DevOps, and Platform Engineers handling production incidents and routine maintenance.

---

## Incident Response Matrix

| Incident Type | Severity | Primary Alert | Runbook Section |
| :--- | :--- | :--- | :--- |
| High API 5xx Error Rate | Critical | `HighAPIErrorRate` | [Runbook 1](#runbook-1-high-api-5xx-error-rate) |
| High API Latency (>1.5s) | Warning | `HighAPILatency` | [Runbook 2](#runbook-2-high-api-latency) |
| PostgreSQL DB Failover / Outage | Critical | `HighDatabaseConnections` | [Runbook 3](#runbook-3-postgresql-database-failover) |
| Qdrant Vector Search Latency / Failure | Warning/Critical | `VectorDBHighLatency` | [Runbook 4](#runbook-4-qdrant-vector-search-failure) |
| Redis Cache Outage / Low Hit Rate | Warning | `LowCacheHitRate` | [Runbook 5](#runbook-5-redis-cache-eviction--outage) |
| Worker Queue Backlog | Warning | Custom Prometheus | [Runbook 6](#runbook-6-worker-queue-backlog) |

---

## Runbook 1: High API 5xx Error Rate

### Symptom
Prometheus fires `HighAPIErrorRate` alert (>5% of HTTP responses returning 5xx status).

### Diagnosis
1. Inspect Grafana dashboard (`RAGTUNE Enterprise AI Platform Overview`).
2. Search Loki logs for 500 error tracebacks:
   ```bash
   kubectl logs -n ragtune-prod -l app.kubernetes.io/component=backend --tail=100 | grep "ERROR"
   ```
3. Check pod status & restarts:
   ```bash
   kubectl get pods -n ragtune-prod -l app.kubernetes.io/component=backend
   ```

### Remediation
1. If pods are crash-looping due to bad release deployment, trigger an immediate rollback:
   ```bash
   kubectl rollout undo deployment/backend -n ragtune-prod
   ```
2. If database connections are failing, restart connection pool or verify RDS health:
   ```bash
   kubectl rollout restart deployment/backend -n ragtune-prod
   ```

---

## Runbook 2: High API Latency

### Symptom
P95 response latency exceeds 1.5 seconds.

### Remediation
1. Check Horizontal Pod Autoscaler (HPA) status:
   ```bash
   kubectl get hpa -n ragtune-prod
   ```
2. Manually scale up backend replicas if required:
   ```bash
   kubectl scale deployment/backend -n ragtune-prod --replicas=10
   ```
3. Check Redis cache hit rate; if hit rate < 50%, verify Redis instance health.

---

## Runbook 3: PostgreSQL Database Failover

### Symptom
Database connection timeout errors.

### Remediation
1. Check PostgreSQL pod/instance status:
   ```bash
   kubectl exec -it postgres-0 -n ragtune-prod -- pg_isready -U ragtune_user -d ragtune_db
   ```
2. In AWS RDS, trigger automated failover to standby replica:
   ```bash
   aws rds reboot-db-instance --db-instance-identifier ragtune-postgres-prod --force-failover
   ```
3. If database data is corrupted, execute Disaster Recovery Restore Script:
   ```bash
   ./scripts/restore_disaster_recovery.sh s3://ragtune-enterprise-storage/backups/postgres/ragtune_db_latest.sql.gz s3://ragtune-enterprise-storage/backups/qdrant/snapshot_latest.snapshot
   ```

---

## Runbook 4: Qdrant Vector Search Failure

### Symptom
Vector similarity search requests timing out or returning HTTP 503.

### Remediation
1. Check Qdrant readiness probe status:
   ```bash
   kubectl get statefulset qdrant -n ragtune-prod
   curl -i http://qdrant-service:6333/healthz
   ```
2. If Qdrant pod memory is exhausted, restart StatefulSet:
   ```bash
   kubectl rollout restart statefulset/qdrant -n ragtune-prod
   ```
3. Restore vector collection snapshot using `./scripts/backup_qdrant.sh` or restore runner.

---

## Runbook 5: Redis Cache Eviction & Outage

### Symptom
Low cache hit rate or connection refused.

### Remediation
1. Flush degraded cache keys:
   ```bash
   redis-cli -h redis-service flushdb
   ```
2. Restart Redis deployment:
   ```bash
   kubectl rollout restart deployment/redis -n ragtune-prod
   ```

---

## Runbook 6: Worker Queue Backlog

### Symptom
Unprocessed background evaluation and indexing task queue backlog building up.

### Remediation
1. Scale up background processing workers:
   ```bash
   kubectl scale deployment/worker -n ragtune-prod --replicas=8
   ```
