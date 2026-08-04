"""
RAGTUNE Enterprise Verification & Quality Assurance Engine - Quality Scoring Engine
Calculates composite Quality Metrics across Groundedness, Faithfulness, Relevance, and Hallucination Risk.
"""

from verification.domain import QualityMetrics


class QualityScoringEngine:
    def compute_metrics(
        self,
        groundedness_score: float,
        citation_coverage: float,
        relevance_score: float,
        hallucination_risk: float,
        latency_ms: float = 0.0,
    ) -> QualityMetrics:
        """
        Computes composite QualityMetrics and overall_quality_score.
        """
        faithfulness = round(
            max(0.0, groundedness_score - (hallucination_risk * 0.5)), 2
        )

        # Weighted composite score
        composite = (
            (groundedness_score * 0.35)
            + (faithfulness * 0.25)
            + (relevance_score * 0.20)
            + ((1.0 - hallucination_risk) * 0.20)
        )
        overall_score = round(min(max(composite, 0.0), 1.0), 2)

        return QualityMetrics(
            groundedness_score=groundedness_score,
            faithfulness_score=faithfulness,
            citation_coverage=citation_coverage,
            relevance_score=relevance_score,
            hallucination_risk=hallucination_risk,
            overall_quality_score=overall_score,
            verification_latency_ms=latency_ms,
        )
