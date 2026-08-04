"""
RAGTUNE Enterprise Verification & Quality Assurance Engine - Decision Matrix Engine
Maps composite quality metrics, CRAG triggers, and risk scores to explicit VerificationAction decisions.
"""


from verification.domain import QualityMetrics, VerificationAction


class DecisionMatrix:
    def map_action(
        self,
        metrics: QualityMetrics,
        should_trigger_crag: bool,
        crag_rationale: str,
        requires_hitl: bool = False,
        hallucination_issues: list[str] = None,
    ) -> tuple[VerificationAction, str]:
        """
        Applies enterprise decision matrix rules to select action and construct explanation.
        """
        hallucination_issues = hallucination_issues or []

        # 1. Check CRAG Selective Re-Retrieval Trigger
        if should_trigger_crag:
            return VerificationAction.TRIGGER_CRAG_RE_RETRIEVAL, crag_rationale

        # 2. Check Human-in-the-Loop Approval Escalation Trigger
        if requires_hitl:
            return (
                VerificationAction.ESCALATE_HITL,
                "Escalated to Human Operator: High risk score or sensitive query flag.",
            )

        # 3. Check High Hallucination Risk
        if metrics.hallucination_risk >= 0.50:
            return (
                VerificationAction.REJECT,
                f"Rejected: High hallucination risk detected ({metrics.hallucination_risk}). Issues: {hallucination_issues}",
            )

        # 4. Check Composite Quality Score Thresholds
        score = metrics.overall_quality_score
        if score >= 0.80:
            return (
                VerificationAction.APPROVE,
                f"Approved: High evidence quality score ({score}) with zero critical issues.",
            )

        if score >= 0.65:
            return (
                VerificationAction.APPROVE_WITH_WARNING,
                f"Approved with Warning: Marginal quality score ({score}). Minor evidence gaps detected.",
            )

        if score >= 0.50:
            return (
                VerificationAction.REGENERATE,
                f"Regeneration Requested: Insufficient answer quality score ({score}).",
            )

        return (
            VerificationAction.REJECT,
            f"Rejected: Failed quality assurance thresholds with score ({score}).",
        )
