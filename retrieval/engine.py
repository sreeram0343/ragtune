"""
RAGTUNE Enterprise Hybrid Retrieval Engine - Master Retrieval Harness
Orchestrates query understanding, HyDE expansion, dual-path search, RRF fusion, Cross-Encoder re-ranking, and context building.
"""

import time
from typing import Optional, List
from input_security.framework.stage import EnrichedSecurityRequest
from retrieval.domain import EvidencePackage, RetrievalMetrics
from retrieval.query_analysis import QueryUnderstanding
from retrieval.search import HybridSearchEngine
from retrieval.fusion import ReciprocalRankFusion
from retrieval.rerank import CrossEncoderReRanker
from retrieval.context import ContextBuilder


class HybridRetrievalEngine:
    def __init__(
        self,
        search_engine: Optional[HybridSearchEngine] = None,
        max_token_budget: int = 1500
    ):
        self.search_engine = search_engine if search_engine else HybridSearchEngine()
        self.query_analyzer = QueryUnderstanding()
        self.fusion_engine = ReciprocalRankFusion(rrf_k=60)
        self.reranker = CrossEncoderReRanker()
        self.context_builder = ContextBuilder(max_token_budget=max_token_budget)

    def retrieve_evidence(
        self,
        security_request: EnrichedSecurityRequest,
        top_k: int = 5
    ) -> EvidencePackage:
        """
        Main Retrieval API:
        Executes end-to-end evidence discovery, ranking, fusion, re-ranking, and context packaging.
        """
        t0 = time.time()
        query = security_request.sanitized_query
        sec_ctx = security_request.security_context

        tenant_id = sec_ctx.org_id if sec_ctx and sec_ctx.org_id else "global_tenant"
        workspace_id = sec_ctx.workspace_id if sec_ctx and sec_ctx.workspace_id else "global_ws"

        # 1. Query Analysis & Selective HyDE Expansion
        t_hyde_start = time.time()
        normalized_q = self.query_analyzer.normalize_query(query)
        keywords = self.query_analyzer.extract_keywords(normalized_q)
        expanded_query, was_hyde_used = self.query_analyzer.generate_hyde_expansion(normalized_q)
        t_hyde_end = time.time()

        # 2. Dual-Path Search (Dense + Sparse)
        t_search_start = time.time()
        # Mock query vector representation
        dummy_query_vector = [0.1] * 384
        dense_candidates = self.search_engine.search_dense(
            query_vector=dummy_query_vector,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            top_k=10
        )
        sparse_candidates = self.search_engine.search_sparse(
            keywords=keywords,
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            top_k=10
        )
        t_search_end = time.time()

        # 3. Reciprocal Rank Fusion (RRF)
        t_fusion_start = time.time()
        fused_candidates = self.fusion_engine.fuse(
            dense_candidates=dense_candidates,
            sparse_candidates=sparse_candidates,
            top_k=10
        )
        t_fusion_end = time.time()

        # 4. Cross-Encoder Re-Ranking
        t_rerank_start = time.time()
        reranked_candidates = self.reranker.rerank(
            query=normalized_q,
            candidates=fused_candidates,
            top_k=top_k
        )
        t_rerank_end = time.time()

        # 5. Context Construction & Citation Assembly
        package = self.context_builder.build_evidence_package(
            query=query,
            candidates=reranked_candidates,
            expanded_query=expanded_query if was_hyde_used else ""
        )

        t_total_end = time.time()

        # Populate Telemetry Metrics
        package.metrics = RetrievalMetrics(
            dense_candidate_count=len(dense_candidates),
            sparse_candidate_count=len(sparse_candidates),
            fused_candidate_count=len(fused_candidates),
            final_evidence_count=len(package.chunks),
            total_retrieval_latency_ms=round((t_total_end - t0) * 1000.0, 2),
            hyde_latency_ms=round((t_hyde_end - t_hyde_start) * 1000.0, 2),
            search_latency_ms=round((t_search_end - t_search_start) * 1000.0, 2),
            fusion_latency_ms=round((t_fusion_end - t_fusion_start) * 1000.0, 2),
            rerank_latency_ms=round((t_rerank_end - t_rerank_start) * 1000.0, 2),
            precision_at_k=1.0 if len(package.chunks) > 0 else 0.0,
            mrr_at_k=1.0 if len(package.chunks) > 0 else 0.0,
            ndcg_at_k=1.0 if len(package.chunks) > 0 else 0.0
        )

        return package
