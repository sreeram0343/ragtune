# RAGTUNE - Enterprise Knowledge Intelligence Platform

![RAGTUNE Platform](https://img.shields.io/badge/RAGTUNE-Enterprise%20v1.0-6366F1?style=for-the-badge)
![Output Governance](https://img.shields.io/badge/Output%20Governance-Zero--Trust%20Redaction-10B981?style=for-the-badge)
![Verification Engine](https://img.shields.io/badge/Verification-Self--RAG%20%2B%20CRAG-10B981?style=for-the-badge)
![Enterprise Text--to--SQL](https://img.shields.io/badge/Text--to--SQL-AST%20Read--Only%20Engine-10B981?style=for-the-badge)
![Hybrid Retrieval](https://img.shields.io/badge/Hybrid%20Retrieval-Dense%20%2B%20BM25%20%2B%20RRF-10B981?style=for-the-badge)
![Intent Router](https://img.shields.io/badge/Intent%20Router-Dynamic%20Planner-10B981?style=for-the-badge)
![LangGraph Orchestration](https://img.shields.io/badge/Orchestration-LangGraph%20StateGraph-10B981?style=for-the-badge)
![Intelligent Cache](https://img.shields.io/badge/Intelligent%20Cache-L1--L2%20Multi--Tier-10B981?style=for-the-badge)
![Input Security Pipeline](https://img.shields.io/badge/Input%20Security-8--Stage%20Defense-10B981?style=for-the-badge)
![IAM & Security](https://img.shields.io/badge/IAM-Production%20Grade-10B981?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-10B981?style=for-the-badge)
![Build Status](https://img.shields.io/badge/Build-Passing-10B981?style=for-the-badge)

RAGTUNE is a domain-agnostic Enterprise Knowledge Intelligence Platform engineered for organizations to query, reason, and execute evidence-backed decisions across structured SQL databases and unstructured enterprise documents.

Unlike simple conversational chatbots, RAGTUNE is a deterministic, secure, and transparent intelligence platform combining an Output Security & Response Governance Engine, a Reflection & Verification Engine (Self-RAG & CRAG), an Enterprise Text-to-SQL Engine, a Production-Grade Hybrid Retrieval Engine, an Intent Router, multi-agent orchestration, an 8-stage Input Security Pipeline, an Intelligent Multi-Layer Caching System, a 9-layer Guardrails system, Explainable AI (XAI) execution tracing, and Human-in-the-Loop (HITL) approval workflows.

![RAGTUNE Dashboard Interface](docs/images/dashboard.png)

---

## Table of Contents
- [Platform Architecture](#platform-architecture)
- [Output Security & Response Governance Engine](#output-security--response-governance-engine)
- [Reflection, Verification & Quality Assurance Engine](#reflection-verification--quality-assurance-engine)
- [Enterprise Text-to-SQL Engine](#enterprise-text-to-sql-engine)
- [Enterprise Hybrid Retrieval Engine](#enterprise-hybrid-retrieval-engine)
- [Intent Router & Query Planning Engine](#intent-router--query-planning-engine)
- [Workflow Orchestration Engine](#workflow-orchestration-engine)
- [Intelligent Caching System](#intelligent-caching-system)
- [Input Security Pipeline](#input-security-pipeline)
- [Enterprise IAM & Multi-Tenancy](#enterprise-iam--multi-tenancy)
- [9-Layer Enterprise Guardrails Pipeline](#9-layer-enterprise-guardrails-pipeline)
- [Core Technology Stack](#core-technology-stack)
- [Quick Start Guide](#quick-start-guide)
- [REST API Documentation](#rest-api-documentation)
- [License](#license)

---

## Platform Architecture

RAGTUNE is built around an event-driven multi-agent state machine powered by LangGraph. All incoming user requests pass through an Input Security Pipeline, an Intelligent Cache, an Intent Router, Execution Engines, a Verification Engine, and an Output Security & Response Governance Engine.

![RAGTUNE Platform Architecture](docs/images/architecture.png)

```mermaid
graph TD
    Client[Enterprise Web UI / REST API] --> Gateway[FastAPI Gateway & Security Middleware]
    Gateway --> SecurityPipeline[8-Stage Defense-in-Depth Input Security Pipeline]
    SecurityPipeline --> CacheManager[Intelligent Multi-Layer Cache Manager]
    
    CacheManager -- L1/L2 Cache Hit (0.1ms) --> Client
    CacheManager -- Cache Miss --> IntentRouter[Intent Router & Query Planning Engine]
    
    IntentRouter --> ExecPlan[Structured Execution Plan Model]
    ExecPlan --> OrchestrationEngine[LangGraph Workflow Orchestration Engine]
    
    OrchestrationEngine -->|Structured Query| Text2SQL[Enterprise Text-to-SQL Engine]
    OrchestrationEngine -->|Unstructured Query| HybridRetriever[Enterprise Hybrid Retrieval Engine]
    
    Text2SQL --> EvaluationNode[Validation & Quality Evaluation Node]
    HybridRetriever --> EvaluationNode
    
    EvaluationNode --> VerificationEngine[Reflection & Verification QA Engine]
    VerificationEngine --> OutputGovernance[Output Security & Response Governance Engine]
    
    OutputGovernance --> SchemaValidator[Schema & Payload Integrity Validator]
    SchemaValidator --> Moderator[Content Toxicity & Prompt Leakage Moderator]
    Moderator --> PIISecretRedactor[PII & Secret Redactor - Permission Aware]
    PIISecretRedactor --> PolicyEngine[Enterprise Policy & Compliance Engine]
    PolicyEngine --> Formatter[Response Formatter - Markdown / JSON]
    Formatter --> MetadataGen[Governance Metadata Generator]
    MetadataGen --> AuditLog[Immutable Security Auditor]
    
    AuditLog --> Client
```

---

## Output Security & Response Governance Engine

The Output Security & Response Governance Engine (`output_governance/`) serves as the zero-trust final security boundary and decision point before API delivery. No response bypasses this layer.

```mermaid
sequenceDiagram
    participant Verifier as QA Engine
    participant Schema as Schema Validator
    participant Mod as Content Moderator
    participant Redact as Data Redactor
    participant Policy as Policy Engine
    participant Meta as Metadata & Audit
    participant API as Final API Envelope

    Verifier->>Schema: Verified Response + QualityReport
    Schema->>Schema: Check Field Completeness & Schema Integrity
    Schema->>Mod: Scan Narrative Content
    Mod->>Mod: Evaluate Toxicity & System Leakage Rules
    Mod->>Redact: Pass Cleaned Text
    Redact->>Redact: Scan & Redact PII / Secrets / API Keys
    Redact->>Policy: Enforce Workspace & Tenant Compliance Rules
    Policy->>Meta: Format Presentation & Attach Governance Metadata
    Meta->>Meta: Generate Immutable Audit Log Record
    Meta-->>API: Package Governed API Response Envelope
```

### Core Subsystems:
1. **Domain & Envelope Models (`output_governance/domain.py`)**: `PolicyDecision`, `RedactionRecord`, `GovernanceMetadata`, and `GovernedResponseEnvelope`.
2. **Response Schema Validator (`output_governance/validation.py`)**: Enforces response field completeness, citation integrity, and token window bounds.
3. **Content Moderator (`output_governance/moderation.py`)**: Scans narrative text for toxic content, hate speech, system prompt leakage, and model policy violations.
4. **Sensitive Data Redactor (`output_governance/redaction.py`)**: Detects and redacts PII (Emails, Phone numbers, SSNs), API keys, Passwords, and Financial Secrets with permission-aware visibility.
5. **Enterprise Policy Engine (`output_governance/policy.py`)**: Evaluates Organization, Workspace, and Role-Based compliance rules (`ALLOW`, `WARN_AND_ALLOW`, `BLOCK`).
6. **Response Formatter (`output_governance/formatter.py`)**: Formats presentation-independent Markdown, JSON, and Tabular response layouts without modifying reasoning logic.
7. **Governance Metadata Generator (`output_governance/metadata.py`)**: Synthesizes enterprise metadata (Request ID, Workflow ID, Latency, Cost, Quality Score, Audit References).
8. **Master Governance Engine (`output_governance/engine.py`)**: Orchestrates the zero-trust pipeline into a unified `govern_response()` API.

---

## Reflection, Verification & Quality Assurance Engine

The Reflection, Verification & Quality Assurance Engine (`verification/`) evaluates factual grounding, detects hallucinations, performs Self-RAG reflection loops, and triggers Corrective RAG (CRAG) selective re-retrieval when context is insufficient.

---

## Enterprise Text-to-SQL Engine

The Enterprise Text-to-SQL Engine (`text2sql/`) translates natural language analytics questions into validated, read-only SQL queries, executes them securely over relational databases, and packages structured tabular results with data citations and execution statistics.

---

## Enterprise Hybrid Retrieval Engine

The Enterprise Hybrid Retrieval Engine (`retrieval/`) discovers, ranks, re-ranks, and packages grounded evidence chunks from enterprise documents while enforcing multi-tenant row-level security isolation.

---

## Intent Router & Query Planning Engine

The Intent Router and Query Planning Engine (`router/`) acts as the decision-making brain of the platform. Rather than executing query tools directly, it analyzes user intent, discovers available platform capabilities, evaluates cost and latency trade-offs, and outputs a structured **Execution Plan** (`ExecutionPlan`).

---

## Workflow Orchestration Engine

The orchestration engine (`orchestration/`) serves as the central nervous system of the platform. Built using **LangGraph**, it manages workflow lifecycles, node execution, state checkpointing, fault recovery, and Human-in-the-Loop (HITL) approval gates.

---

## Intelligent Caching System

The platform features an intelligent, multi-layer caching architecture (`cache/`) positioned immediately after request validation:

- **Multi-Tenant Key Isolation (`TenantCacheKeyBuilder`)**: Generates SHA-256 keys in format `ragtune:{tenant_id}:{workspace_id}:{namespace}:{hash}`.
- **L1 Exact Match Hash Cache (`InMemoryLRUCacheProvider` / `RedisCacheProvider`)**: Microsecond lookup ($< 0.1\text{ms}$) with thread-safe LRU eviction and sliding/absolute TTL.
- **L2 Semantic Vector Cache (`SemanticCacheEngine`)**: Cosine similarity matching ($\ge 0.92$ threshold) enabling response reuse for semantically equivalent queries.
- **Single-Flight Coalescing (`SingleFlightLock`)**: Prevents cache stampedes by executing duplicate concurrent cache misses exactly once.
- **Tag-Based Invalidation (`CacheInvalidationEngine`)**: Event-driven cache purging listening for system events (`document:updated`, `schema:changed`, `user:permissions_changed`, `workspace:deleted`).

---

## Input Security Pipeline

All inbound requests enter the system through a centralized 8-stage Defense-in-Depth pipeline (`input_security/`):

| Stage | Security Stage Name | Technical Scope & Responsibilities |
| :--- | :--- | :--- |
| **Stage 1** | **Payload & Schema Validation** | Enforces 2MB maximum payload size limits, validates JSON syntax, and blocks path traversal attempts (`../`). |
| **Stage 2** | **Authentication & Session Verification** | Validates Bearer access tokens, verifies signature claims, checks DB session revocation, and enforces account active status. |
| **Stage 3** | **Multi-Tenant RBAC Authorization** | Evaluates Organization and Workspace roles against target endpoint permissions to enforce tenant isolation. |
| **Stage 4** | **Rate Limiting & Token Budgeting** | Tracks request velocity (max 60 req/min) and caps input token counts (max 4,000 tokens) to prevent Denial-of-Wallet attacks. |
| **Stage 5** | **Request Normalization & Sanitization** | Applies NFKC Unicode normalization, strips zero-width space bypasses, and sanitizes XSS script tags. |
| **Stage 6** | **Prompt Inspection & Jailbreak Defense** | Inspects query text for direct/indirect prompt injection, adversarial roleplay (DAN), and system instruction overrides. |
| **Stage 7** | **PII & PHI Detection & Anonymization** | Detects and dynamically redacts Emails, Phone Numbers, SSNs, Credit Cards, and IP Addresses. |
| **Stage 8** | **Risk Scoring & Context Enrichment** | Calculates cumulative threat risk score (0-100), assigns Trust Level (HIGH, MEDIUM, LOW, UNTRUSTED), and enriches request context. |

---

## Enterprise IAM & Multi-Tenancy

The platform identity architecture provides a production-ready trust boundary:

- **Multi-Tenant Hierarchy**: Strict isolation across Organization, Workspace, Project, and User entities.
- **Cryptographic Security**: PBKDF2-HMAC-SHA256 password hashing (600,000 rounds) with random salts and SHA-256 token digest storage.
- **Refresh Token Rotation (RTR)**: Every token refresh invalidates the prior refresh token and issues a new pair.
- **Instant Security Revocation**: Password changes or administrative account suspensions instantly revoke active sessions.
- **Role-Based Access Control (RBAC)**: Fine-grained permission matrices checking Organization Roles and Workspace Roles.

---

## 9-Layer Enterprise Guardrails Pipeline

RAGTUNE enforces a 9-layer security boundary evaluated across pre-execution and post-execution phases:

| Layer | Guardrail Name | Scope | Technical Description |
| :--- | :--- | :--- | :--- |
| **L1** | **Prompt Injection Defense** | Pre-Execution | Scans incoming queries for jailbreak patterns and adversarial prompt payloads. |
| **L2** | **PII & PHI Anonymization** | Pre-Execution | Identifies and dynamically masks Emails, Phone Numbers, SSNs, Credit Cards, and IP Addresses. |
| **L3** | **Domain Scope Boundary** | Pre-Execution | Validates that queries align with enterprise business domains and rejects off-topic requests. |
| **L4** | **RBAC & Tenant Isolation** | Pre-Execution | Verifies caller permissions and restricts multi-tenant database table access. |
| **L5** | **Semantic Drift Guard** | Post-Execution | Measures context-query embedding overlap to detect and prevent semantic hallucination drift. |
| **L6** | **SQL AST Safety & Limit Capper** | Pre/Post Execution | AST parsing via `sqlglot` to strictly enforce read-only SELECT statements and cap query result limits. |
| **L7** | **Groundedness & NLI Citation** | Post-Execution | Evaluates sentence-by-sentence factual grounding against source evidence. |
| **L8** | **Toxicity & Harm Filter** | Post-Execution | Scans output content for profane, harmful, toxic, or discriminatory terminology. |
| **L9** | **Data Leakage Scanner** | Post-Execution | Prevents leakage of internal credentials, API keys, passwords, or system prompt instructions. |

---

## Core Technology Stack

- **Backend Gateway**: FastAPI, Pydantic v2, Uvicorn
- **Output Security & Response Governance Engine**: Response Schema Validator, Content Moderator, Sensitive Data Redactor, Policy Engine, Governance Metadata Generator
- **Reflection & Verification Engine**: Self-RAG Reflection Subsystem, CRAG Evaluator, Groundedness Verifier, Hallucination Detector
- **Enterprise Text-to-SQL Engine**: AST Parser (`sqlglot`), Schema Introspector, Read-Only SQLExecutionEngine
- **Hybrid Retrieval Engine**: Dense Vector Search, BM25 Lexical Sparse Search, RRF Fusion ($k=60$), Cross-Encoder Re-Ranker
- **Intent Router & Planner**: Dynamic Capability Registry, Pattern Intent Classifier, Strategy Decision Engine
- **Orchestration Engine**: LangGraph StateGraph Framework, State Checkpointer
- **Intelligent Caching System**: L1 Exact Match LRU Cache, L2 Cosine Semantic Vector Cache, Single-Flight Coalescing Lock
- **Input Security Pipeline**: 8-Stage Defense-in-Depth Framework, Unicode NFKC, Regex Threat Classifiers
- **Database Persistence**: SQLAlchemy 2.0, SQLite / PostgreSQL
- **SQL Parser**: SQLGlot AST Engine
- **Frontend Dashboard**: HTML5, Vanilla CSS Glassmorphism, Modern SPA Architecture

---

## Quick Start Guide

### 1. Installation
Clone the repository and install the dependencies:

```bash
git clone https://github.com/sreeram0343/ragtune.git
cd ragtune
pip install -r requirements.txt
```

### 2. Seed Enterprise Demo Data
Generate the pre-seeded SQLite enterprise database and sample knowledge documents:

```bash
python main.py --seed
```

### 3. Launch Web Platform & Gateway Server
Start the platform on `http://localhost:8000`:

```bash
python main.py
```

Access the interactive Web Dashboard in your browser: `http://localhost:8000`

### 4. Run Standalone CLI Query
Execute an intelligence query via the command line interface:

```bash
python main.py --query "What is our uptime commitment for Acme Enterprise under SLA terms?"
```

### 5. Run Automated Test Suite
Execute the full test suite covering Output Governance, Reflection & Verification, Text-to-SQL, Hybrid Retrieval, Intent Router & Planning, LangGraph Workflow Orchestration, Intelligent Cache, Input Security Pipeline, IAM, authentication, token rotation, RBAC, guardrails, agents, and REST APIs:

```bash
python -m pytest tests/ -v
```

---

## REST API Documentation

### Authentication & IAM Endpoints
- `POST /api/v1/auth/register`: User registration with password strength validation.
- `POST /api/v1/auth/login`: Authenticates credentials and issues Access + Refresh Tokens.
- `POST /api/v1/auth/refresh`: Refresh Token Rotation (RTR).
- `POST /api/v1/auth/logout`: Revokes active session.
- `POST /api/v1/auth/logout-all`: Revokes all user sessions across all devices.
- `GET /api/v1/auth/me`: Returns user profile and active SecurityContext permissions.
- `POST /api/v1/auth/password/change`: Password update with session revocation.
- `POST /api/v1/auth/organizations`: Creates Organization and default Workspace.
- `POST /api/v1/auth/invitations`: Issues secure invitation token.
- `POST /api/v1/auth/invitations/accept`: Accepts invitation token.
- `GET /api/v1/auth/audit-logs`: Queries immutable security audit log history.
- `POST /api/v1/auth/admin/users/{user_id}/suspend`: Administrative account suspension.

### Query Intelligence Endpoints
- `POST /api/v1/query`: Submits query to multi-agent reasoning engine.
- `POST /api/v1/ingest/text`: Ingests document snippets into hybrid vector retriever.
- `GET /api/v1/schema`: Returns introspected database tables and column schemas.
- `GET /api/v1/hitl/queue`: Lists pending Human-in-the-Loop review tickets.
- `POST /api/v1/hitl/action`: Approves or rejects pending HITL tickets.
- `GET /api/v1/xai/{trace_id}`: Retrieves step-by-step XAI execution graph.
- `GET /api/v1/cache/stats`: Returns cache performance telemetry.

---

## License

Released under the MIT License. Built for enterprise knowledge intelligence.
