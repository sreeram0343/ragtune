"""
RAGTUNE - Cross-Encoder & Re-Ranking Engine
Re-ranks hybrid search candidates using feature-based relevance scoring.
"""

import re
from typing import Any

from config.settings import settings


class CrossEncoderReranker:
    def __init__(self):
        pass

    def _calculate_cross_relevance_score(
        self, query: str, content: str, title: str
    ) -> float:
        """
        Calculates cross-feature relevance score between query and document text.
        """
        q_lower = query.lower()
        c_lower = content.lower()
        t_lower = title.lower()

        q_words = set(re.findall(r"\w+", q_lower))
        c_words = set(re.findall(r"\w+", c_lower))

        if not q_words:
            return 0.0

        # Exact word overlap ratio
        word_overlap = len(q_words.intersection(c_words)) / len(q_words)

        # Title match bonus
        title_bonus = 0.2 if any(w in t_lower for w in q_words) else 0.0

        # Exact phrase match bonus
        phrase_bonus = 0.3 if q_lower in c_lower else 0.0

        total_score = (word_overlap * 0.5) + title_bonus + phrase_bonus
        return float(min(1.0, total_score))

    def rerank(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        top_k: int = settings.TOP_K_RERANK,
    ) -> list[dict[str, Any]]:
        """
        Re-ranks top candidates and returns sorted top_k evidence items.
        """
        if not candidates:
            return []

        reranked = []
        for cand in candidates:
            cross_score = self._calculate_cross_relevance_score(
                query, cand["content"], cand["title"]
            )
            # Combine original RRF score with cross-encoder relevance score
            final_relevance = (cand.get("rrf_score", 0.0) * 0.4) + (cross_score * 0.6)
            item = dict(cand)
            item["rerank_score"] = float(final_relevance)
            item["cross_score"] = float(cross_score)
            reranked.append(item)

        # Sort by rerank_score descending
        reranked.sort(key=lambda x: x["rerank_score"], reverse=True)

        # Re-assign final rank
        final_top = reranked[:top_k]
        for idx, item in enumerate(final_top, start=1):
            item["final_rank"] = idx

        return final_top
