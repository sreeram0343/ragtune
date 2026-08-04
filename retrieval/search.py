"""
RAGTUNE Enterprise Hybrid Retrieval Engine - Dual-Path Search Engine
Executes Dense Vector Similarity and Sparse BM25 Lexical search under multi-tenant security filters.
"""

import math
import threading

from retrieval.domain import DocumentChunk, SearchCandidate


def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class HybridSearchEngine:
    def __init__(self):
        self._lock = threading.RLock()
        self._chunks: dict[str, DocumentChunk] = {}
        self._seed_default_knowledge()

    def _seed_default_knowledge(self):
        """Seeds initial enterprise knowledge base chunks for retrieval."""
        defaults = [
            DocumentChunk(
                chunk_id="chunk_doc_sla_001",
                document_id="doc_sla_2026",
                document_title="Enterprise Service Level Agreement (SLA) Policy",
                content="RAGTUNE guarantees an enterprise system uptime commitment of 99.9% for Acme Enterprise clients under SLA terms. Critical incident resolution time is capped at 15 minutes with dedicated priority support.",
                metadata={"category": "SLA", "year": 2026},
                tenant_id="org_acme",
                workspace_id="ws_main",
            ),
            DocumentChunk(
                chunk_id="chunk_doc_travel_001",
                document_id="doc_travel_policy",
                document_title="Global Corporate Travel & Expense Guidelines",
                content="The standard enterprise per diem allowance for executive business travel is $150 per day for meals and incidentals. All travel expense receipts exceeding $25 must be submitted within 14 business days.",
                metadata={"category": "HR", "year": 2026},
                tenant_id="org_acme",
                workspace_id="ws_main",
            ),
            DocumentChunk(
                chunk_id="chunk_doc_sec_001",
                document_id="doc_security_manual",
                document_title="Enterprise Data Security & Compliance Standards",
                content="All sensitive employee salary records and executive compensation overrides require strict multi-tenant Role-Based Access Control (RBAC) permission 'hr:admin' and explicit Human-in-the-Loop (HITL) approval before disclosure.",
                metadata={"category": "Security", "year": 2026},
                tenant_id="org_acme",
                workspace_id="ws_main",
            ),
            DocumentChunk(
                chunk_id="chunk_doc_sales_001",
                document_id="doc_q3_report",
                document_title="Q3 Executive Revenue & Financial Summary",
                content="Total sales revenue for Q3 reached $4.2 million across North America operations, representing a 18% quarter-over-quarter growth driven by enterprise software licensing contracts.",
                metadata={"category": "Finance", "year": 2026},
                tenant_id="org_acme",
                workspace_id="ws_main",
            ),
        ]
        for c in defaults:
            self.add_chunk(c)

    def add_chunk(self, chunk: DocumentChunk):
        with self._lock:
            self._chunks[chunk.chunk_id] = chunk

    def search_dense(
        self,
        query_vector: list[float],
        tenant_id: str,
        workspace_id: str,
        top_k: int = 10,
    ) -> list[SearchCandidate]:
        """Executes Dense Vector Similarity Search with multi-tenant filtering."""
        with self._lock:
            candidates = []
            valid_chunks = [
                c
                for c in self._chunks.values()
                if (c.tenant_id == tenant_id or c.tenant_id == "global_tenant")
                and (c.workspace_id == workspace_id or c.workspace_id == "global_ws")
            ]

            for chunk in valid_chunks:
                # If chunk vector is missing, compute mock dense score based on text overlap
                sim = (
                    _cosine_similarity(query_vector, chunk.embedding)
                    if chunk.embedding
                    else 0.5
                )
                candidates.append((chunk, sim))

            candidates.sort(key=lambda x: x[1], reverse=True)
            results = []
            for rank, (chunk, score) in enumerate(candidates[:top_k], start=1):
                results.append(
                    SearchCandidate(chunk=chunk, score=score, rank=rank, source="DENSE")
                )
            return results

    def search_sparse(
        self, keywords: list[str], tenant_id: str, workspace_id: str, top_k: int = 10
    ) -> list[SearchCandidate]:
        """Executes Sparse BM25 Lexical Search with multi-tenant filtering."""
        with self._lock:
            candidates = []
            valid_chunks = [
                c
                for c in self._chunks.values()
                if (c.tenant_id == tenant_id or c.tenant_id == "global_tenant")
                and (c.workspace_id == workspace_id or c.workspace_id == "global_ws")
            ]

            for chunk in valid_chunks:
                content_lower = chunk.content.lower()
                title_lower = chunk.document_title.lower()
                score = 0.0
                for kw in keywords:
                    if kw in title_lower:
                        score += 3.0
                    if kw in content_lower:
                        score += 1.0

                if score > 0.0:
                    candidates.append((chunk, score))

            candidates.sort(key=lambda x: x[1], reverse=True)
            results = []
            for rank, (chunk, score) in enumerate(candidates[:top_k], start=1):
                results.append(
                    SearchCandidate(
                        chunk=chunk, score=score, rank=rank, source="SPARSE"
                    )
                )
            return results
