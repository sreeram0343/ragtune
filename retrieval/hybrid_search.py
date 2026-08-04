"""
RAGTUNE - Hybrid Retrieval Engine
Coordinates BM25 sparse and dense vector search with Reciprocal Rank Fusion (RRF).
"""

import os
from typing import Any

from config.settings import settings
from storage.document_processor import DocumentProcessor
from storage.vector_store import HybridVectorStore


class HybridSearchEngine:
    def __init__(
        self,
        vector_store: HybridVectorStore,
        docs_dir: str = "demo_data/sample_documents",
    ):
        self.vector_store = vector_store
        self.doc_processor = DocumentProcessor()
        self.docs_dir = docs_dir
        self._ensure_documents_indexed()

    def _ensure_documents_indexed(self):
        """Indexes sample documents automatically if vector store is unpopulated."""
        if len(self.vector_store.chunks) == 0 and os.path.exists(self.docs_dir):
            for fname in os.listdir(self.docs_dir):
                fpath = os.path.join(self.docs_dir, fname)
                if os.path.isfile(fpath):
                    try:
                        chunks = self.doc_processor.process_file(fpath)
                        self.vector_store.add_chunks(chunks)
                    except Exception:
                        pass

    def search(
        self,
        query: str,
        top_k: int = settings.TOP_K_DENSE,
        rrf_k: float = settings.RRF_K,
        min_score: float = 0.001,
    ) -> list[dict[str, Any]]:
        """
        Executes hybrid retrieval and returns structured document evidence objects.
        """
        self._ensure_documents_indexed()
        hybrid_results = self.vector_store.search_hybrid(
            query=query, top_k=top_k, rrf_k=rrf_k
        )

        formatted_results: list[dict[str, Any]] = []

        for rank, (chunk, score) in enumerate(hybrid_results, start=1):
            if score < min_score:
                continue

            formatted_results.append(
                {
                    "rank": rank,
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "title": chunk.title,
                    "content": chunk.content,
                    "rrf_score": float(score),
                    "token_count": chunk.token_count,
                    "metadata": chunk.metadata,
                }
            )

        return formatted_results
