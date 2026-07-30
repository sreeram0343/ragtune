# RAGTUNE Enterprise - Production Deployment Guide

This guide provides step-by-step instructions for deploying the **RAGTUNE Enterprise AI Platform** into production using Docker Compose for local enterprise stacks, Kubernetes (EKS/AKS/GKE) for cloud orchestration, and Terraform for Infrastructure as Code (IaC).

---

## 1. Local Enterprise Setup (Docker Compose)

The local enterprise stack orchestrates 10 microservices: Nginx Frontend, FastAPI Backend Engine, Background AI Processing Worker, PostgreSQL 16, Qdrant Vector DB, Redis 7 Multi-Layer Cache, MinIO Object Storage, Prometheus, Grafana, and Loki.

### Quickstart Command
```bash
# Clone repository
git clone https://github.com/sreeram0343/ragtune.git
cd ragtune

# Start the full enterprise stack
docker compose up -d --build
```

### Accessing Local Services
- **Frontend Dashboard**: `http://localhost:8080`
- **FastAPI OpenAPI Documentation**: `http://localhost:8000/docs`
- **Health Endpoint**: `http://localhost:8000/api/v1/health`
- **Grafana Observability**: `http://localhost:3000` (User: `admin`, Pass: `ragtune_grafana_pass_2026`)
- **Prometheus Metrics**: `http://localhost:9090`
- **MinIO Object Storage Console**: `http://localhost:9001` (User: `ragtune_minio_admin`, Pass: `ragtune_minio_secret_key_2026`)
- **Qdrant Vector DB Dashboard**: `http://localhost:6333/dashboard`

---

## 2. Cloud Infrastructure Provisioning (Terraform)

Terraform provisions multi-AZ cloud resources (AWS EKS, RDS PostgreSQL, ElastiCache Redis, S3 Object Storage with KMS Encryption).

### Commands
```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Validate IaC syntax
terraform validate

# Plan infrastructure deployment
terraform plan -out=tfplan

# Apply infrastructure changes
terraform apply tfplan
```

---

## 3. Production Kubernetes Deployment (Kubectl & Helm)

### Deployment Steps
```bash
# 1. Connect to your K8s Cluster
aws eks update-kubeconfig --region us-east-1 --name ragtune-production-cluster

# 2. Apply Namespace and Configurations
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/serviceaccounts-rbac.yaml
kubectl apply -f k8s/network-policy.yaml

# 3. Deploy Stateful Storage Services
kubectl apply -f k8s/postgres-statefulset.yaml
kubectl apply -f k8s/qdrant-statefulset.yaml
kubectl apply -f k8s/redis-deployment.yaml

# 4. Deploy Stateless Application Workloads
kubectl apply -f k8s/deployment.yaml          # Backend API Engine
kubectl apply -f k8s/frontend-deployment.yaml # Frontend Web Server
kubectl apply -f k8s/worker-deployment.yaml   # Background Processing Pool

# 5. Apply Networking Services & Ingress
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml

# 6. Apply Auto-Scaling & High Availability Policies
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/pdb.yaml

# 7. Verify Rollout Status
kubectl rollout status deployment/backend -n ragtune-prod
kubectl rollout status deployment/frontend -n ragtune-prod
```

---

## 4. Post-Deployment Verification & Load Testing

Execute live smoke verification and load testing scripts:

```bash
# Smoke Verification
python scripts/verify_deployment.py --url https://ragtune.enterprise.com

# Load & Performance Benchmark
python scripts/load_test.py --url https://ragtune.enterprise.com --requests 100 --concurrency 10
```
