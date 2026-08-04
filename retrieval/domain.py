"""
RAGTUNE Enterprise Hybrid Retrieval Engine - Domain Models & Data Structures
Defines document chunk schemas, search candidates, evidence packages, and retrieval metrics.
"""

from typing import Any

from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str
    content: str
    embedding: list[float] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tenant_id: str = "global_tenant"
    workspace_id: str = "global_ws"


class SearchCandidate(BaseModel):
    chunk: DocumentChunk
    score: float
    rank: int
    source: str  # "DENSE", "SPARSE", or "FUSED"


class CitationReference(BaseModel):
    citation_id: str
    document_title: str
    document_id: str
    chunk_id: str
    snippet: str


class RetrievalMetrics(BaseModel):
    dense_candidate_count: int = 0
    sparse_candidate_count: int = 0
    fused_candidate_count: int = 0
    final_evidence_count: int = 0
    total_retrieval_latency_ms: float = 0.0
    hyde_latency_ms: float = 0.0
    search_latency_ms: float = 0.0
    fusion_latency_ms: float = 0.0
    rerank_latency_ms: float = 0.0
    precision_at_k: float = 1.0
    mrr_at_k: float = 1.0
    ndcg_at_k: float = 1.0


class EvidencePackage(BaseModel):
    query: str
    expanded_query: str | None = None
    chunks: list[DocumentChunk] = Field(default_factory=list)
    citations: list[CitationReference] = Field(default_factory=list)
    retrieval_confidence: float = 1.0
    total_tokens_used: int = 0
    metrics: RetrievalMetrics = Field(default_factory=RetrievalMetrics)
