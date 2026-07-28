"""
RAGTUNE - Test Suite for Hybrid Search & Re-Ranking Engine
"""

import pytest
from storage.document_processor import DocumentProcessor
from storage.vector_store import HybridVectorStore
from retrieval.hybrid_search import HybridSearchEngine
from retrieval.reranker import CrossEncoderReranker


def test_hybrid_search_and_rerank():
    proc = DocumentProcessor(chunk_size=100, overlap=10)
    store = HybridVectorStore()

    chunks = proc.process_text(
        text="RAGTUNE provides 99.99% uptime commitment under Platinum SLA terms.",
        doc_id="doc_sla",
        title="Enterprise SLA Policy"
    )
    store.add_chunks(chunks)

    retriever = HybridSearchEngine(store)
    results = retriever.search("What is the uptime under Platinum SLA?", top_k=5)

    assert len(results) > 0
    assert results[0]["title"] == "Enterprise SLA Policy"

    reranker = CrossEncoderReranker()
    reranked = reranker.rerank("Platinum SLA uptime", results, top_k=3)

    assert len(reranked) > 0
    assert "rerank_score" in reranked[0]
