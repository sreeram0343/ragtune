# Enterprise Security & Zero-Trust Governance Policy

## 1. Data Classification & Access Control
All customer data stored within RAGTUNE is classified under Tier-1 Enterprise Confidentiality. Multi-Tenant Role-Based Access Control (RBAC) enforces strict isolation across workspaces and tenant IDs.

## 2. Cryptographic Standards
Data at rest is encrypted using AES-256-GCM. Data in transit across internal services and API endpoints requires Istio mTLS with TLS 1.3 encryption.

## 3. Input Security & Threat Defense
All incoming user prompts pass through an 8-Stage Security Pipeline including Unicode NFKC normalization, Regex SQL Injection scanning, Prompt Injection defense, and PII anonymization.
