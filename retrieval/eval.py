"""
RAGTUNE Enterprise Hybrid Retrieval Engine - IR Evaluation Subsystem
Calculates Information Retrieval metrics including Precision@K, Recall@K, MRR, and nDCG.
"""

import math

from retrieval.domain import SearchCandidate


class RetrievalEvaluator:
    @staticmethod
    def calculate_precision_at_k(
        retrieved: list[SearchCandidate], relevant_ids: set[str], k: int = 5
    ) -> float:
        """Calculates Precision@K = (Relevant & Retrieved) / K."""
        if not retrieved or k <= 0:
            return 0.0
        top_k = retrieved[:k]
        hits = sum(1 for c in top_k if c.chunk.chunk_id in relevant_ids)
        return hits / float(min(k, len(top_k)))

    @staticmethod
    def calculate_mrr_at_k(
        retrieved: list[SearchCandidate], relevant_ids: set[str], k: int = 5
    ) -> float:
        """Calculates Mean Reciprocal Rank MRR@K = 1 / rank_of_first_hit."""
        if not retrieved or k <= 0:
            return 0.0
        for rank, candidate in enumerate(retrieved[:k], start=1):
            if candidate.chunk.chunk_id in relevant_ids:
                return 1.0 / float(rank)
        return 0.0

    @staticmethod
    def calculate_ndcg_at_k(
        retrieved: list[SearchCandidate], relevant_ids: set[str], k: int = 5
    ) -> float:
        """Calculates Normalized Discounted Cumulative Gain (nDCG@K)."""
        if not retrieved or k <= 0 or not relevant_ids:
            return 0.0

        dcg = 0.0
        for rank, candidate in enumerate(retrieved[:k], start=1):
            if candidate.chunk.chunk_id in relevant_ids:
                dcg += 1.0 / math.log2(rank + 1)

        # Calculate Ideal DCG (IDCG)
        idcg = sum(
            1.0 / math.log2(r + 1) for r in range(1, min(len(relevant_ids), k) + 1)
        )
        if idcg == 0.0:
            return 0.0

        return dcg / idcg
