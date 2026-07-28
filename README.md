# RAGTUNE - Enterprise Knowledge Intelligence Platform

![RAGTUNE Platform](https://img.shields.io/badge/RAGTUNE-Enterprise%20v1.0-6366F1?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)
![Build Status](https://img.shields.io/badge/Build-Passing-10B981?style=for-the-badge)
![Python Version](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge)

**RAGTUNE** is an enterprise-grade, domain-agnostic Knowledge Intelligence Platform engineered for organizations to query, reason, and execute evidence-backed decisions across structured SQL databases and unstructured enterprise documents.

This is **NOT** a simple chatbot. It is a deterministic, secure, and transparent Enterprise Intelligence Platform combining:

- **Multi-Agent LangGraph Orchestration**: Dynamic routing across specialized reasoning nodes.
- **Text-to-SQL Synthesis**: Schema introspection, SQL AST validation, and automated self-repair.
- **Hybrid Search & Cross-Encoder Re-Ranking**: Dense vector embeddings + BM25 sparse index combined via Reciprocal Rank Fusion (RRF).
- **9-Layer Enterprise Guardrails Pipeline**: Pre/post execution security matrix protecting PII, preventing prompt injection, enforcing read-only SQL, and blocking hallucinations.
- **Explainable AI (XAI)**: Full step-by-step visual execution graphs, timing metrics, and citation attributions.
- **Human-in-the-Loop (HITL)**: Interactive operator review queue for low-confidence or policy-triggered queries.
- **Redis & Multi-Tier Caching**: Semantic vector caching and SQL result caching with TTL.

---

## 📋 Table of Contents
- [Architecture Overview](#-architecture-overview)
- [9-Layer Enterprise Guardrails Pipeline](#-9-layer-enterprise-guardrails-pipeline)
- [Quick Start Guide](#-quick-start-guide)
- [REST API Documentation](#-rest-api-documentation)
- [License](#-license)

---

## 🏛️ Architecture Overview

```mermaid
graph TD
    Client[Enterprise Web UI / REST API] --> Gateway[FastAPI Gateway & Auth Middleware]
    Gateway --> Cache[Redis Multi-Tier Cache]
    Cache -- Cache Hit (0ms) --> Client
    Cache -- Cache Miss --> G_Pre[Guardrails L1-L4: Injection, PII, Scope, RBAC]
    
    G_Pre --> Router[Intent Router Agent]
    
    Router -->|Structured Query| SQLAgent[Text-to-SQL Engine]
    Router -->|Unstructured Query| RAGAgent[Hybrid RAG Engine]
    Router -->|Hybrid Query| FusionAgent[Evidence Fusion Agent]
    
    SQLAgent --> SQLGuard[L6: SQL AST Safety & Limit Capper]
    SQLGuard --> DB[(Structured SQL Database)]
    
    RAGAgent --> BM25[BM25 Sparse Index]
    RAGAgent --> Dense[Dense Vector Store]
    BM25 --> RRF[Reciprocal Rank Fusion]
    Dense --> RRF
    RRF --> ReRanker[Cross-Encoder Re-Ranker]
    
    DB --> FusionAgent
    ReRanker --> FusionAgent
    
    FusionAgent --> G_Post[Guardrails L5, L7-L9: Drift, Groundedness, Toxicity, Leakage]
    
    G_Post -- Safe & High Confidence --> XAI[Explainable AI Trace Generator]
    G_Post -- Flagged / Low Confidence --> HITL[Human-in-the-Loop Review Queue]
    
    HITL -- Approved by Operator --> XAI
    XAI --> Client
```

---

## 🛡️ 9-Layer Enterprise Guardrails Pipeline

| Layer | Guardrail Name | Scope | Description |
| :--- | :--- | :--- | :--- |
| **L1** | **Prompt Injection Defense** | Pre-Execution | Scans queries for adversarial payloads, jailbreaks, and system overrides. |
| **L2** | **PII & PHI Anonymization** | Pre-Execution | Detects and dynamically masks Emails, Phone numbers, SSNs, Credit Cards, and IPs. |
| **L3** | **Domain Scope Boundary** | Pre-Execution | Ensures user queries remain strictly within enterprise business domain boundaries. |
| **L4** | **RBAC & Tenant Isolation** | Pre-Execution | Validates user role permissions and restricts multi-tenant table access. |
| **L5** | **Semantic Drift Guard** | Post-Execution | Measures context-query embedding overlap to prevent semantic hallucination drift. |
| **L6** | **SQL AST Safety & Capper** | Pre/Post Execution | Enforces read-only `SELECT` queries, rejects DDL/DML, and caps `LIMIT` bounds. |
| **L7** | **Groundedness & NLI Citation** | Post-Execution | Evaluates sentence-by-sentence factual grounding against source evidence. |
| **L8** | **Toxicity & Harm Filter** | Post-Execution | Scans output content for profane, harmful, or discriminatory terminology. |
| **L9** | **Data Leakage Scanner** | Post-Execution | Prevents leakage of internal credentials, API keys, or system prompt instructions. |

---

## 🚀 Quick Start Guide

### 1. Installation
Ensure Python 3.11+ is installed. Clone the repository and install dependencies:

```bash
git clone https://github.com/sreeram0343/ragtune.git
cd ragtune
pip install -r requirements.txt
```

### 2. Seed Enterprise Demo Data
Generate the sample SQLite enterprise database and document knowledge files:

```bash
python main.py --seed
```

### 3. Launch Web Platform & Gateway Server
Start the platform on `http://localhost:8000`:

```bash
python main.py
```

Access the interactive web dashboard at: `http://localhost:8000`

### 4. Run CLI Query
Execute a standalone intelligence query via command line:

```bash
python main.py --query "What is our uptime commitment for Acme Enterprise under SLA terms?"
```

### 5. Run Automated Test Suite
Run unit and integration tests covering guardrails, Text-to-SQL, hybrid search, agents, and REST API:

```bash
python -m pytest tests/ -v
```

---

## 📡 REST API Documentation

### Query Intelligence Endpoint
- **URL**: `POST /api/v1/query`
- **Request Body**:
```json
{
  "query": "What were total sales for Acme Enterprise in 2024?",
  "role": "ANALYST",
  "tenant_id": "tenant_enterprise_default"
}
```

### Document Ingestion Endpoint
- **URL**: `POST /api/v1/ingest/text`
- **Request Body**:
```json
{
  "text": "Enterprise travel policy allows $85 per diem for domestic meals.",
  "title": "Travel Policy Amendment 2026"
}
```

### Additional Endpoints
- `GET /api/v1/schema`: Returns introspected database tables and column schemas.
- `GET /api/v1/hitl/queue`: Lists pending Human-in-the-Loop review tickets.
- `POST /api/v1/hitl/action`: Resolves pending tickets with operator approval/rejection.
- `GET /api/v1/xai/{trace_id}`: Retrieves step-by-step XAI execution graph.
- `GET /api/v1/cache/stats`: Returns cache telemetry.

---

## 📄 License
Released under the MIT License. Built for enterprise knowledge intelligence.
