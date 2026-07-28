"""
RAGTUNE Enterprise Verification & Quality Assurance Engine - Corrective RAG (CRAG) Evaluator
Evaluates evidence quality scores and determines if selective re-retrieval (CRAG) is required.
"""

from typing import List, Tuple


class CRAGEvaluator:
    def evaluate_evidence_sufficiency(
        self,
        query: str,
        source_contexts: List[str],
        groundedness_score: float
    ) -> Tuple[bool, str]:
        """
        Evaluates context relevance and quality.
        Returns (should_trigger_crag_re_retrieval, rationale).
        """
        if not source_contexts or len(source_contexts) == 0:
            return True, "CRAG Triggered: Zero source document contexts retrieved."

        total_context_len = sum(len(c.strip()) for c in source_contexts)
        if total_context_len < 30:
            return True, "CRAG Triggered: Retrieved evidence text is too short to support reasoning."

        if groundedness_score < 0.40:
            return True, f"CRAG Triggered: Groundedness score ({groundedness_score}) falls below CRAG threshold (0.40)."

        return False, "Evidence context is sufficient for reasoning."
