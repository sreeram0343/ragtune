"""
RAGTUNE Enterprise Hybrid Retrieval Engine - Comprehensive Test Suite
Tests HyDE query expansion, dense/sparse search, RRF fusion, Cross-Encoder re-ranking, token budgeting, and IR metrics.
"""

import json

from auth.domain.models import SecurityContext, UserStatus
from input_security.framework.stage import (
    EnrichedSecurityRequest,
    SecurityRequestContainer,
    TrustLevel,
)
from retrieval import (
    ContextBuilder,
    DocumentChunk,
    HybridRetrievalEngine,
    HybridSearchEngine,
    ReciprocalRankFusion,
    RetrievalEvaluator,
    SearchCandidate,
)


def _build_dummy_security_request(
    query: str, org_id="org_acme", workspace_id="ws_main"
) -> EnrichedSecurityRequest:
    sec_ctx = SecurityContext(
        user_id="usr_retrieval_test",
        email="retrieval@enterprise.com",
        status=UserStatus.ACTIVE,
        org_id=org_id,
        workspace_id=workspace_id,
        permissions={"workspace:read"},
    )

    container = SecurityRequestContainer(
        raw_body=json.dumps({"query": query}).encode("utf-8"),
        user_query=query,
        user_context=sec_ctx,
    )

    return EnrichedSecurityRequest(
        request_id="req_ret_001",
        original_container=container,
        sanitized_query=query,
        sanitized_payload={"query": query},
        security_context=sec_ctx,
        trust_level=TrustLevel.HIGH,
        cumulative_risk_score=0.0,
        cleared_for_orchestration=True,
    )


def test_end_to_end_hybrid_retrieval():
    engine = HybridRetrievalEngine()
    req = _build_dummy_security_request(
        "What is our enterprise SLA commitment for Acme?"
    )

    package = engine.retrieve_evidence(req, top_k=5)

    assert package.query == "What is our enterprise SLA commitment for Acme?"
    assert len(package.chunks) >= 1
    assert len(package.citations) >= 1
    assert package.retrieval_confidence > 0.0
    assert package.total_tokens_used > 0
    assert package.metrics.total_retrieval_latency_ms >= 0.0


def test_reciprocal_rank_fusion_rrf():
    fusion = ReciprocalRankFusion(rrf_k=60)
    chunk1 = DocumentChunk(
        chunk_id="c1",
        document_id="d1",
        document_title="Doc 1",
        content="SLA commitment 99.9%",
    )
    chunk2 = DocumentChunk(
        chunk_id="c2",
        document_id="d2",
        document_title="Doc 2",
        content="Travel per diem $150",
    )

    dense = [SearchCandidate(chunk=chunk1, score=0.9, rank=1, source="DENSE")]
    sparse = [
        SearchCandidate(chunk=chunk2, score=3.0, rank=1, source="SPARSE"),
        SearchCandidate(chunk=chunk1, score=1.0, rank=2, source="SPARSE"),
    ]

    fused = fusion.fuse(dense, sparse, top_k=5)

    assert len(fused) == 2
    # chunk1 appeared in both dense and sparse, so RRF score should be highest
    assert fused[0].chunk.chunk_id == "c1"


def test_context_builder_token_budget_and_deduplication():
    builder = ContextBuilder(max_token_budget=50)  # Very tight token budget
    chunk1 = DocumentChunk(
        chunk_id="c1",
        document_id="d1",
        document_title="Doc 1",
        content="Short snippet 1",
    )
    chunk2 = DocumentChunk(
        chunk_id="c2",
        document_id="d2",
        document_title="Doc 2",
        content="Duplicate snippet",
        content_hash=1,
    )
    chunk3 = DocumentChunk(
        chunk_id="c3",
        document_id="d3",
        document_title="Doc 3",
        content="Duplicate snippet",
        content_hash=1,
    )

    candidates = [
        SearchCandidate(chunk=chunk1, score=0.9, rank=1, source="RERANKED"),
        SearchCandidate(chunk=chunk2, score=0.8, rank=2, source="RERANKED"),
        SearchCandidate(chunk=chunk3, score=0.7, rank=3, source="RERANKED"),
    ]

    package = builder.build_evidence_package("test query", candidates)

    # Should deduplicate chunk3 because content is identical to chunk2
    chunk_ids = [c.chunk_id for c in package.chunks]
    assert "c3" not in chunk_ids


def test_multi_tenant_workspace_security_isolation():
    search = HybridSearchEngine()

    # Attempt search from different org/workspace
    res_other = search.search_sparse(
        keywords=["sla"], tenant_id="org_other", workspace_id="ws_other", top_k=5
    )
    # Acme SLA chunk should not leak to org_other
    chunk_ids = [c.chunk.chunk_id for c in res_other]
    assert "chunk_doc_sla_001" not in chunk_ids


def test_ir_evaluation_metrics():
    evaluator = RetrievalEvaluator()
    chunk1 = DocumentChunk(
        chunk_id="c1", document_id="d1", document_title="Doc 1", content="Content 1"
    )
    chunk2 = DocumentChunk(
        chunk_id="c2", document_id="d2", document_title="Doc 2", content="Content 2"
    )

    retrieved = [
        SearchCandidate(chunk=chunk1, score=0.9, rank=1, source="RERANKED"),
        SearchCandidate(chunk=chunk2, score=0.8, rank=2, source="RERANKED"),
    ]
    relevant = {"c1"}

    p5 = evaluator.calculate_precision_at_k(retrieved, relevant, k=5)
    mrr = evaluator.calculate_mrr_at_k(retrieved, relevant, k=5)
    ndcg = evaluator.calculate_ndcg_at_k(retrieved, relevant, k=5)

    assert p5 == 0.5  # 1 relevant out of 2 retrieved
    assert mrr == 1.0  # Rank 1 hit
    assert ndcg > 0.0
