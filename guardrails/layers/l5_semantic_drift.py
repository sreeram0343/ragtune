"""
RAGTUNE - Guardrail Layer 5: Semantic Drift & Out-of-Scope Query Detector
Measures query-context similarity and semantic alignment.
"""




class SemanticDriftGuard:
    def evaluate_drift(
        self,
        query: str,
        context_snippets: list[str] | None = None,
        threshold: float = 0.3,
    ) -> tuple[bool, float, str]:
        """
        Evaluates semantic alignment between query and retrieved context snippets.
        """
        if not query or not query.strip():
            return False, 0.0, "Empty query provided"

        if not context_snippets:
            # No context to compare against (e.g. pure SQL query route), default pass
            return True, 0.85, "No text context required for semantic drift evaluation"

        # Token overlap heuristic as efficient proxy for semantic similarity
        query_words = set(query.lower().split())
        context_words = set(" ".join(context_snippets).lower().split())

        overlap = query_words.intersection(context_words)
        overlap_score = len(overlap) / max(len(query_words), 1)

        if overlap_score < threshold and len(query_words) > 3:
            return (
                False,
                float(overlap_score),
                f"Semantic drift detected (low context token alignment score: {overlap_score:.2f} vs threshold {threshold})",
            )

        return True, float(min(1.0, overlap_score + 0.5)), "Semantic drift check passed"
