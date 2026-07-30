# RAGTUNE Enterprise - Cloud Architecture & Security Architecture

This document describes the high-availability cloud deployment architecture, network security topology, zero-trust container security policies, encryption models, and access governance controls implemented for **RAGTUNE**.

---

## 1. High-Level Architecture Topology

```
                         +-----------------------------------+
                         |    Cloudflare CDN / Route53 DNS   |
                         +-----------------------------------+
                                           |
                                      (HTTPS / TLS)
                                           v
                         +-----------------------------------+
                         |       AWS ALB / Ingress Controller|
                         +-----------------------------------+
                                           |
                    +----------------------+----------------------+
                    | (Static Assets)                             | (API Proxy)
                    v                                             v
       +-------------------------+                   +-------------------------+
       |   Nginx Frontend Pods   |                   |   FastAPI Backend Pods  |
       |  (HPA: 2 - 10 replicas) |                   |  (HPA: 3 - 20 replicas) |
       +-------------------------+                   +-------------------------+
                                                                  |
              +-----------------------+---------------------------+-----------------------+
              |                       |                           |                       |
              v                       v                           v                       v
       +-------------+         +-------------+             +--------------+        +-------------+
       | PostgreSQL  |         | Qdrant DB   |             | Redis Cache  |        | MinIO / S3  |
       | Multi-AZ DB |         | StatefulSet |             | Replication  |        | Encrypted   |
       +-------------+         +-------------+             +--------------+        +-------------+
```

---

## 2. Zero-Trust Container & Network Security

### Container Security Controls
- **Non-Root Execution**: All containers execute with unprivileged user accounts (`uid: 10001` for Python backend/workers, `uid: 101` for Nginx frontend).
- **Immutable Root Filesystem**: Write permissions to container filesystems are strictly restricted.
- **Capabilities Dropped**: Linux kernel capabilities are set to `drop: [ALL]`.
- **Image Scanning**: Automated vulnerability scans with Trivy in CI/CD block images containing CRITICAL or HIGH vulnerabilities.

### Kubernetes Network Microsegmentation
- **Default Deny Policy**: `NetworkPolicy` defaults to denying all ingress and egress traffic.
- **Explicit Ingress Rules**:
  - Frontend accepts traffic strictly on port `8080` from Ingress.
  - Backend API accepts incoming requests exclusively from Frontend pods on port `8000`.
  - PostgreSQL DB accepts TCP `5432` only from Backend and Worker pods.
  - Qdrant Vector DB accepts `6333`/`6334` only from Backend and Worker pods.
  - Redis Cache accepts `6379` only from Backend and Worker pods.

---

## 3. Data Protection & Encryption

- **Encryption at Rest**:
  - PostgreSQL RDS volumes encrypted with AWS KMS AES-256 keys.
  - Qdrant vector storage encrypted via EBS volume encryption.
  - S3 Object Storage enforced with KMS Server-Side Encryption (`aws:kms`).
- **Encryption in Transit**:
  - Ingress enforces TLS 1.3/1.2 HTTPS for external web traffic.
  - Internal pod-to-pod communication encrypted via mutual TLS (mTLS).

---

## 4. RBAC & Identity Security

- **Principle of Least Privilege**:
  - Kubernetes workloads run with dedicated `ServiceAccounts`.
  - RBAC `Role` and `RoleBinding` restrict workload permissions to minimal read-only scope for ConfigMaps and Secrets.
- **JWT Authentication & RBAC**:
  - FastAPI backend enforces JWT token validation and role-based access checks (`ADMIN`, `ANALYST`, `AUDITOR`, `VIEWER`).

---

## 5. High Availability & Scaling Parameters

- **Stateful Failover**: Multi-AZ PostgreSQL RDS and Redis Replication Groups support automated failover (< 30 seconds RTO).
- **Stateless Horizontal Scaling**:
  - Backend HPA triggers scaling up to 20 pods at 75% CPU / 80% Memory utilization.
  - Frontend HPA triggers scaling up to 10 pods at 70% CPU utilization.
- **Pod Disruption Budgets (PDB)**: Guarantees at least 2 Backend pods and 1 Frontend pod remain active during cluster upgrades.
