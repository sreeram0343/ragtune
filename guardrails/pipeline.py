"""
RAGTUNE - 9-Layer Enterprise Guardrails Pipeline Orchestrator
Sequentially runs pre-execution and post-execution security boundaries.
"""

from pydantic import BaseModel, Field

from config.settings import settings
from guardrails.layers.l1_injection import InjectionGuard
from guardrails.layers.l2_pii_masking import PIIMaskingGuard
from guardrails.layers.l3_domain_boundary import DomainBoundaryGuard
from guardrails.layers.l4_rbac_isolation import RBACIsolationGuard
from guardrails.layers.l5_semantic_drift import SemanticDriftGuard
from guardrails.layers.l6_sql_safety import SQLSafetyGuard
from guardrails.layers.l7_groundedness import GroundednessGuard
from guardrails.layers.l8_toxicity_safety import ToxicitySafetyGuard
from guardrails.layers.l9_data_leakage import DataLeakageGuard
from security.rbac import UserContext


class LayerResult(BaseModel):
    layer_name: str
    layer_num: int
    passed: bool
    score: float
    details: str
    sanitized_output: str | None = None


class PipelineResult(BaseModel):
    all_passed: bool
    overall_confidence: float
    pre_execution_passed: bool
    post_execution_passed: bool
    sanitized_query: str
    sanitized_sql: str | None = None
    sanitized_response: str | None = None
    layer_evaluations: list[LayerResult] = Field(default_factory=list)
    hitl_triggered: bool = False
    hitl_reason: str | None = None


class GuardrailPipeline:
    def __init__(self):
        self.l1_injection = InjectionGuard()
        self.l2_pii = PIIMaskingGuard()
        self.l3_domain = DomainBoundaryGuard()
        self.l4_rbac = RBACIsolationGuard()
        self.l5_drift = SemanticDriftGuard()
        self.l6_sql = SQLSafetyGuard()
        self.l7_groundedness = GroundednessGuard()
        self.l8_toxicity = ToxicitySafetyGuard()
        self.l9_leakage = DataLeakageGuard()

    def run_pre_execution(
        self, query: str, user_context: UserContext
    ) -> PipelineResult:
        """
        Runs pre-execution guardrails (Layers 1 to 4).
        """
        evals: list[LayerResult] = []

        # Layer 1: Prompt Injection
        l1_pass, l1_score, l1_det = self.l1_injection.evaluate(query)
        evals.append(
            LayerResult(
                layer_name="L1: Prompt Injection",
                layer_num=1,
                passed=l1_pass,
                score=l1_score,
                details=l1_det,
            )
        )

        # Layer 2: PII Masking
        l2_pass, l2_score, masked_query, l2_det = self.l2_pii.evaluate(query)
        evals.append(
            LayerResult(
                layer_name="L2: PII Masking",
                layer_num=2,
                passed=l2_pass,
                score=l2_score,
                details=l2_det,
                sanitized_output=masked_query,
            )
        )

        # Layer 3: Domain Boundary
        l3_pass, l3_score, l3_det = self.l3_domain.evaluate(masked_query)
        evals.append(
            LayerResult(
                layer_name="L3: Domain Boundary",
                layer_num=3,
                passed=l3_pass,
                score=l3_score,
                details=l3_det,
            )
        )

        # Layer 4: RBAC & Tenant Isolation
        l4_pass, l4_score, l4_det = self.l4_rbac.evaluate_query_permission(
            user_context, "QUERY_KNOWLEDGE"
        )
        evals.append(
            LayerResult(
                layer_name="L4: RBAC Isolation",
                layer_num=4,
                passed=l4_pass,
                score=l4_score,
                details=l4_det,
            )
        )

        pre_passed = all(e.passed for e in evals)
        avg_score = sum(e.score for e in evals) / len(evals) if evals else 1.0

        return PipelineResult(
            all_passed=pre_passed,
            overall_confidence=float(avg_score),
            pre_execution_passed=pre_passed,
            post_execution_passed=True,
            sanitized_query=masked_query,
            layer_evaluations=evals,
            hitl_triggered=not pre_passed,
            hitl_reason=(
                "Pre-execution guardrails violation" if not pre_passed else None
            ),
        )

    def run_post_execution(
        self,
        pre_result: PipelineResult | None,
        user_context: UserContext,
        generated_sql: str | None = None,
        retrieved_chunks: list[str] | None = None,
        raw_response: str | None = None,
    ) -> PipelineResult:
        """
        Runs post-execution guardrails (Layers 5 to 9).
        """
        if pre_result is None:
            pre_result = PipelineResult(
                all_passed=True,
                overall_confidence=1.0,
                pre_execution_passed=True,
                post_execution_passed=True,
                sanitized_query=raw_response or "",
            )
        evals = list(pre_result.layer_evaluations)
        sanitized_sql = generated_sql

        # Layer 5: Semantic Drift
        l5_pass, l5_score, l5_det = self.l5_drift.evaluate_drift(
            pre_result.sanitized_query, retrieved_chunks
        )
        evals.append(
            LayerResult(
                layer_name="L5: Semantic Drift",
                layer_num=5,
                passed=l5_pass,
                score=l5_score,
                details=l5_det,
            )
        )

        # Layer 6: SQL Execution Safety
        if generated_sql:
            l6_pass, l6_score, safe_sql, l6_det = self.l6_sql.evaluate_sql(
                generated_sql
            )
            sanitized_sql = safe_sql
            evals.append(
                LayerResult(
                    layer_name="L6: SQL Safety",
                    layer_num=6,
                    passed=l6_pass,
                    score=l6_score,
                    details=l6_det,
                    sanitized_output=safe_sql,
                )
            )
        else:
            evals.append(
                LayerResult(
                    layer_name="L6: SQL Safety",
                    layer_num=6,
                    passed=True,
                    score=1.0,
                    details="No SQL generated",
                )
            )

        # Layer 7: Hallucination & Groundedness
        sanitized_resp = raw_response or ""
        if raw_response and retrieved_chunks:
            l7_pass, l7_score, l7_det, _ = self.l7_groundedness.evaluate_groundedness(
                raw_response,
                retrieved_chunks,
                threshold=settings.GROUNDEDNESS_THRESHOLD,
            )
            evals.append(
                LayerResult(
                    layer_name="L7: Groundedness Verification",
                    layer_num=7,
                    passed=l7_pass,
                    score=l7_score,
                    details=l7_det,
                )
            )
        else:
            evals.append(
                LayerResult(
                    layer_name="L7: Groundedness Verification",
                    layer_num=7,
                    passed=True,
                    score=1.0,
                    details="Groundedness bypassed (direct response)",
                )
            )

        # Layer 8: Toxicity & Harm Safety
        l8_pass, l8_score, l8_det = self.l8_toxicity.evaluate(sanitized_resp)
        evals.append(
            LayerResult(
                layer_name="L8: Toxicity & Bias",
                layer_num=8,
                passed=l8_pass,
                score=l8_score,
                details=l8_det,
            )
        )

        # Layer 9: Data Leakage Scanner
        l9_pass, l9_score, l9_det = self.l9_leakage.evaluate(sanitized_resp)
        evals.append(
            LayerResult(
                layer_name="L9: Data Leakage Filter",
                layer_num=9,
                passed=l9_pass,
                score=l9_score,
                details=l9_det,
            )
        )

        all_passed = all(e.passed for e in evals)
        avg_score = sum(e.score for e in evals) / len(evals) if evals else 1.0

        hitl_reason = None
        if not all_passed:
            failed_layers = [e.layer_name for e in evals if not e.passed]
            hitl_reason = (
                f"Post-execution guardrail violation on: {', '.join(failed_layers)}"
            )

        return PipelineResult(
            all_passed=all_passed,
            overall_confidence=float(avg_score),
            pre_execution_passed=pre_result.pre_execution_passed,
            post_execution_passed=all(e.passed for e in evals[4:]),
            sanitized_query=pre_result.sanitized_query,
            sanitized_sql=sanitized_sql,
            sanitized_response=sanitized_resp,
            layer_evaluations=evals,
            hitl_triggered=not all_passed
            or avg_score < settings.HITL_CONFIDENCE_THRESHOLD,
            hitl_reason=hitl_reason
            or (
                "Low confidence score trigger"
                if avg_score < settings.HITL_CONFIDENCE_THRESHOLD
                else None
            ),
        )

    def get_failed_layers(self, result: PipelineResult) -> list[str]:
        """Returns the names of all guardrail layers that failed evaluation."""
        return [e.layer_name for e in result.layer_evaluations if not e.passed]

