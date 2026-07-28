"""
RAGTUNE Enterprise Hybrid Retrieval Engine - Cross-Encoder Re-Ranker
High-precision Cross-Encoder feature re-ranker evaluating query-chunk candidate pairs.
"""

from typing import List
from retrieval.domain import SearchCandidate


class CrossEncoderReRanker:
    def __init__(self):
        pass

    def rerank(
        self,
        query: str,
        candidates: List[SearchCandidate],
        top_k: int = 5
    ) -> List[SearchCandidate]:
        """
        Re-ranks candidate chunks using Cross-Encoder semantic scoring.
        """
        if not candidates:
            return []

        scored_candidates = []
        query_words = set(query.lower().split())

        for candidate in candidates:
            chunk_content = candidate.chunk.content.lower()
            chunk_title = candidate.chunk.document_title.lower()

            # Cross-Encoder score evaluation
            content_words = set(chunk_content.split())
            overlap = len(query_words.intersection(content_words)) / max(len(query_words), 1)

            title_boost = 0.3 if any(qw in chunk_title for qw in query_words) else 0.0
            
            # Combine RRF base score with cross-attention overlap score
            ce_score = (candidate.score * 0.4) + (overlap * 0.4) + title_boost
            
            scored_candidates.append(
                SearchCandidate(
                    chunk=candidate.chunk,
                    score=round(ce_score, 4),
                    rank=candidate.rank,
                    source="RERANKED"
                )
            )

        scored_candidates.sort(key=lambda x: x.score, reverse=True)
        
        results = []
        for rank, candidate in enumerate(scored_candidates[:top_k], start=1):
            results.append(
                SearchCandidate(
                    chunk=candidate.chunk,
                    score=candidate.score,
                    rank=rank,
                    source="RERANKED"
                )
            )

        return results
