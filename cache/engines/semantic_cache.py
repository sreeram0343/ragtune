"""
RAGTUNE Intelligent Caching System - Semantic Cache Engine
Performs vector cosine similarity matching (threshold >= 0.92) to reuse near-duplicate query responses.
"""

import math
import threading
import time
from typing import Any


class SemanticCacheEngine:
    def __init__(self, similarity_threshold: float = 0.92, max_entries: int = 2000):
        self.threshold = similarity_threshold
        self.max_entries = max_entries
        self._lock = threading.RLock()
        # Structure: list of dicts {tenant_id, workspace_id, query_text, embedding, cached_result, created_at, tags}
        self._entries: list[dict[str, Any]] = []

    def _cosine_similarity(self, vec_a: list[float], vec_b: list[float]) -> float:
        if not vec_a or not vec_b or len(vec_a) != len(vec_b):
            return 0.0
        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)

    def _heuristic_embedding(self, text: str) -> list[float]:
        """Generates deterministic 64-dimensional feature vector for text matching if no external model is provided."""
        text_clean = text.lower().strip()
        dims = [0.0] * 64
        for i, char in enumerate(text_clean):
            idx = (ord(char) * (i + 1)) % 64
            dims[idx] += 1.0
        norm = math.sqrt(sum(x * x for x in dims))
        if norm > 0:
            dims = [x / norm for x in dims]
        return dims

    def lookup(
        self,
        tenant_id: str,
        workspace_id: str,
        query_text: str,
        embedding: list[float] | None = None,
    ) -> tuple[Any, float] | None:
        """
        Looks up semantically similar query within tenant & workspace boundary.
        Returns: (cached_result, similarity_score) if score >= threshold.
        """
        with self._lock:
            if not query_text or not self._entries:
                return None

            query_vec = (
                embedding if embedding else self._heuristic_embedding(query_text)
            )
            best_match: dict[str, Any] | None = None
            highest_sim = 0.0

            for entry in self._entries:
                if (
                    entry["tenant_id"] == tenant_id
                    and entry["workspace_id"] == workspace_id
                ):
                    sim = self._cosine_similarity(query_vec, entry["embedding"])
                    if sim > highest_sim:
                        highest_sim = sim
                        best_match = entry

            if highest_sim >= self.threshold and best_match:
                return best_match["cached_result"], round(highest_sim, 4)

            return None

    def store(
        self,
        tenant_id: str,
        workspace_id: str,
        query_text: str,
        cached_result: Any,
        embedding: list[float] | None = None,
        tags: list[str] | None = None,
    ):
        """Stores a new query embedding & result in the semantic cache."""
        with self._lock:
            query_vec = (
                embedding if embedding else self._heuristic_embedding(query_text)
            )

            # Evict oldest entry if at capacity
            if len(self._entries) >= self.max_entries:
                self._entries.pop(0)

            self._entries.append(
                {
                    "tenant_id": tenant_id,
                    "workspace_id": workspace_id,
                    "query_text": query_text,
                    "embedding": query_vec,
                    "cached_result": cached_result,
                    "created_at": time.time(),
                    "tags": tags or [],
                }
            )

    def invalidate_by_tag(self, tag: str) -> int:
        with self._lock:
            count = 0
            new_entries = []
            for entry in self._entries:
                if tag in entry.get("tags", []):
                    count += 1
                else:
                    new_entries.append(entry)
            self._entries = new_entries
            return count

    def clear(self):
        with self._lock:
            self._cache_entries = []
            self._entries.clear()
