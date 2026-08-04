"""
RAGTUNE Input Security Pipeline - Stage 8: Risk Scoring & Context Enrichment
Aggregates stage threat scores, calculates trust levels, and produces EnrichedSecurityRequest.
"""

import time
import uuid

from input_security.framework.stage import (
    BaseSecurityStage,
    EnrichedSecurityRequest,
    SecurityRequestContainer,
    SecurityViolationException,
    StageResult,
    TrustLevel,
)

CUMULATIVE_RISK_THRESHOLD = 75.0


class RiskScoringEnrichmentStage(BaseSecurityStage):
    def __init__(self):
        super().__init__(stage_id=8, stage_name="Risk Scoring & Context Enrichment")

    def process_enrichment(
        self, container: SecurityRequestContainer, stage_results: list[StageResult]
    ) -> EnrichedSecurityRequest:
        t0 = time.time()

        # Calculate Cumulative Threat Risk Score
        cumulative_risk = sum(r.threat_score for r in stage_results)

        # Assign Trust Level
        if cumulative_risk < 15.0:
            trust_level = TrustLevel.HIGH
        elif cumulative_risk < 40.0:
            trust_level = TrustLevel.MEDIUM
        elif cumulative_risk < 75.0:
            trust_level = TrustLevel.LOW
        else:
            trust_level = TrustLevel.UNTRUSTED

        # Trigger Security Violation if cumulative risk exceeds threshold
        if cumulative_risk >= CUMULATIVE_RISK_THRESHOLD:
            raise SecurityViolationException(
                message=f"Request blocked due to high cumulative threat risk score ({cumulative_risk:.1f}/100)",
                status_code=400,
                stage_name=self.stage_name,
                risk_score=cumulative_risk,
            )

        req_id = f"req_sec_{uuid.uuid4().hex[:12]}"
        query_text = container.user_query or str(
            container.parsed_payload.get("query", "")
        )

        total_latency = sum(r.execution_time_ms for r in stage_results) + (
            (time.time() - t0) * 1000
        )

        return EnrichedSecurityRequest(
            request_id=req_id,
            original_container=container,
            sanitized_query=query_text,
            sanitized_payload=container.parsed_payload,
            security_context=container.user_context,
            trust_level=trust_level,
            cumulative_risk_score=round(cumulative_risk, 2),
            stage_evaluations=stage_results,
            total_latency_ms=round(total_latency, 2),
            cleared_for_orchestration=True,
        )

    def process(self, container: SecurityRequestContainer) -> StageResult:
        # Dummy process implementation to satisfy BaseSecurityStage contract
        return StageResult(
            stage_id=self.stage_id,
            stage_name=self.stage_name,
            passed=True,
            threat_score=0.0,
            audit_notes=["Risk scoring evaluated"],
        )
