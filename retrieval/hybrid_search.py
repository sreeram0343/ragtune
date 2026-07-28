"""
RAGTUNE - Hybrid Retrieval Engine
Coordinates BM25 sparse and dense vector search with Reciprocal Rank Fusion (RRF).
"""

from typing import List, Tuple, Dict, Any, Optional
from storage.vector_store import HybridVectorStore
from storage.document_processor import DocumentChunk
from config.settings import settings


class HybridSearchEngine:
    def __init__(self, vector_store: HybridVectorStore):
        self.vector_store = vector_store

    def search(
        self,
        query: str,
        top_k: int = settings.TOP_K_DENSE,
        rrf_k: float = settings.RRF_K,
        min_score: float = 0.001
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval and returns structured document evidence objects.
        """
        hybrid_results = self.vector_store.search_hybrid(
            query=query, top_k=top_k, rrf_k=rrf_k
        )

        formatted_results: List[Dict[str, Any]] = []

        for rank, (chunk, score) in enumerate(hybrid_results, start=1):
            if score < min_score:
                continue

            formatted_results.append({
                "rank": rank,
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "title": chunk.title,
                "content": chunk.content,
                "rrf_score": float(score),
                "token_count": chunk.token_count,
                "metadata": chunk.metadata
            })

        return formatted_results
