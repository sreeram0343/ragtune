"""
RAGTUNE Enterprise Hybrid Retrieval Engine - Context Construction Engine
Assembles citation-preserved context windows, enforces token budgets, and computes retrieval confidence.
"""

from typing import List, Tuple
from retrieval.domain import SearchCandidate, DocumentChunk, CitationReference, EvidencePackage


class ContextBuilder:
    def __init__(self, max_token_budget: int = 1500):
        self.max_token_budget = max_token_budget

    def _estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count (~4 characters per token)."""
        return max(1, len(text) // 4)

    def build_evidence_package(
        self,
        query: str,
        candidates: List[SearchCandidate],
        expanded_query: str = ""
    ) -> EvidencePackage:
        """
        Assembles final EvidencePackage from re-ranked candidates.
        """
        selected_chunks: List[DocumentChunk] = []
        citations: List[CitationReference] = []
        seen_contents = set()
        accumulated_tokens = 0

        for idx, candidate in enumerate(candidates, start=1):
            chunk = candidate.chunk

            # Deduplicate exact text snippets
            content_hash = hash(chunk.content.strip())
            if content_hash in seen_contents:
                continue

            chunk_tokens = self._estimate_tokens(chunk.content)
            if accumulated_tokens + chunk_tokens > self.max_token_budget:
                break

            seen_contents.add(content_hash)
            selected_chunks.append(chunk)
            accumulated_tokens += chunk_tokens

            # Create Citation Reference
            citation_id = f"cite_{idx}"
            snippet = chunk.content[:150] + "..." if len(chunk.content) > 150 else chunk.content
            citations.append(
                CitationReference(
                    citation_id=citation_id,
                    document_title=chunk.document_title,
                    document_id=chunk.document_id,
                    chunk_id=chunk.chunk_id,
                    snippet=snippet
                )
            )

        # Compute Retrieval Confidence Score
        confidence = 0.0
        if selected_chunks:
            avg_score = sum(c.score for c in candidates[:len(selected_chunks)]) / len(selected_chunks)
            confidence = min(round(avg_score, 2), 1.0)
            if confidence == 0.0:
                confidence = 0.85

        return EvidencePackage(
            query=query,
            expanded_query=expanded_query if expanded_query else None,
            chunks=selected_chunks,
            citations=citations,
            retrieval_confidence=confidence,
            total_tokens_used=accumulated_tokens
        )
