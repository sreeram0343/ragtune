"""
RAGTUNE Enterprise Verification & Quality Assurance Engine - Master Verification Harness
Orchestrates groundedness checking, Self-RAG reflection, hallucination detection, CRAG evaluation, and decision mapping.
"""

import time
import uuid
from typing import List, Optional
from input_security.framework.stage import EnrichedSecurityRequest
from verification.domain import QualityReport, VerificationAction
from verification.grounding import GroundednessVerifier
from verification.self_rag import SelfRAGReflector
from verification.hallucination import HallucinationDetector
from verification.crag import CRAGEvaluator
from verification.scoring import QualityScoringEngine
from verification.decision import DecisionMatrix


class VerificationEngine:
    def __init__(self):
        self.grounding_verifier = GroundednessVerifier()
        self.self_rag_reflector = SelfRAGReflector()
        self.hallucination_detector = HallucinationDetector()
        self.crag_evaluator = CRAGEvaluator()
        self.scoring_engine = QualityScoringEngine()
        self.decision_matrix = DecisionMatrix()

    def verify_response(
        self,
        security_request: EnrichedSecurityRequest,
        response_narrative: str,
        source_contexts: List[str],
        custom_risk_override: Optional[float] = None
    ) -> QualityReport:
        """
        Main Verification API:
        Executes end-to-end response reflection, verification, hallucination scanning, and quality decision mapping.
        """
        t0 = time.time()
        report_id = f"report_{uuid.uuid4().hex[:12]}"
        query = security_request.sanitized_query

        # 1. Groundedness & Citation Coverage Verification
        claims, groundedness_score, citation_coverage = self.grounding_verifier.verify_grounding(
            response_narrative=response_narrative,
            source_contexts=source_contexts
        )

        # 2. Self-RAG Reflection Tokens
        reflection_tokens = self.self_rag_reflector.reflect(
            query=query,
            response_narrative=response_narrative,
            claims=claims
        )
        rel_token = next((t for t in reflection_tokens if t.token_type == "[IS_RELEVANT]"), None)
        relevance_score = rel_token.score if rel_token else 0.90

        # 3. Hallucination & Discrepancy Detection
        hallucination_risk, issues = self.hallucination_detector.detect_hallucination_risk(
            response_narrative=response_narrative,
            source_contexts=source_contexts,
            claims=claims
        )

        # 4. Corrective RAG (CRAG) Sufficiency Evaluation
        should_crag, crag_rationale = self.crag_evaluator.evaluate_evidence_sufficiency(
            query=query,
            source_contexts=source_contexts,
            groundedness_score=groundedness_score
        )

        # 5. Composite Quality Scoring
        t_latency = round((time.time() - t0) * 1000.0, 2)
        metrics = self.scoring_engine.compute_metrics(
            groundedness_score=groundedness_score,
            citation_coverage=citation_coverage,
            relevance_score=relevance_score,
            hallucination_risk=hallucination_risk,
            latency_ms=t_latency
        )

        # 6. Decision Matrix Mapping
        requires_hitl = (security_request.cumulative_risk_score > 40.0) or ("sensitive" in query.lower())
        action, explanation = self.decision_matrix.map_action(
            metrics=metrics,
            should_trigger_crag=should_crag,
            crag_rationale=crag_rationale,
            requires_hitl=requires_hitl,
            hallucination_issues=issues
        )

        return QualityReport(
            report_id=report_id,
            natural_query=query,
            response_narrative=response_narrative,
            action=action,
            quality_score=metrics.overall_quality_score,
            claims=claims,
            reflection_tokens=reflection_tokens,
            metrics=metrics,
            explanation=explanation
        )
