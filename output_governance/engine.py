"""
RAGTUNE Output Security & Response Governance Engine - Master Governance Harness
Exposes unified govern_response API orchestrating schema validation, moderation, redaction, policy enforcement, and metadata packaging.
"""

import time
import uuid

from input_security.framework.stage import EnrichedSecurityRequest
from output_governance.domain import GovernedResponseEnvelope, PolicyDecision
from output_governance.formatter import ResponseFormatter
from output_governance.metadata import MetadataGenerator
from output_governance.moderation import OutputContentModerator
from output_governance.policy import EnterprisePolicyEngine
from output_governance.redaction import SensitiveDataRedactor
from output_governance.validation import ResponseSchemaValidator


class OutputGovernanceEngine:
    def __init__(self):
        self.validator = ResponseSchemaValidator()
        self.moderator = OutputContentModerator()
        self.redactor = SensitiveDataRedactor()
        self.policy_engine = EnterprisePolicyEngine()
        self.formatter = ResponseFormatter()
        self.metadata_generator = MetadataGenerator()

    def govern_response(
        self,
        security_request: EnrichedSecurityRequest,
        raw_response_narrative: str,
        citations: list[str] | None = None,
        quality_score: float = 1.0,
    ) -> GovernedResponseEnvelope:
        """
        Main Output Governance API:
        Validates schema, moderates content, redacts PII/secrets, evaluates policy, and returns GovernedResponseEnvelope.
        """
        t0 = time.time()
        governed_id = f"gov_{uuid.uuid4().hex[:12]}"
        sec_ctx = security_request.security_context

        # 1. Schema Validation
        is_valid_schema, schema_err = self.validator.validate_schema(
            raw_response_narrative
        )
        if not is_valid_schema:
            metadata = self.metadata_generator.generate_metadata(
                security_request=security_request,
                total_latency_ms=(time.time() - t0) * 1000.0,
                quality_score=0.0,
            )
            return GovernedResponseEnvelope(
                governed_id=governed_id,
                status="FAILED",
                formatted_content=schema_err,
                metadata=metadata,
                policy_decision=PolicyDecision.BLOCK,
                explanation=schema_err,
            )

        # 2. Content Moderation & Prompt Leakage Check
        is_clean, violations = self.moderator.moderate_content(raw_response_narrative)

        # 3. PII & Secret Redaction (Permission-Aware)
        sanitized_narrative, redaction_records = self.redactor.sanitize_output(
            content=raw_response_narrative, security_context=sec_ctx
        )

        # 4. Enterprise Policy Evaluation
        policy_decision, policy_explanation = self.policy_engine.evaluate_policy(
            content=sanitized_narrative,
            security_context=sec_ctx,
            moderation_violations=violations,
        )

        # 5. Response Formatting
        formatted_content = self.formatter.format_markdown(
            content=sanitized_narrative, citations=citations
        )

        # 6. Governance Metadata & Audit Reference Packaging
        t_total_ms = (time.time() - t0) * 1000.0
        metadata = self.metadata_generator.generate_metadata(
            security_request=security_request,
            total_latency_ms=t_total_ms,
            quality_score=quality_score,
            citation_count=len(citations) if citations else 0,
        )

        return GovernedResponseEnvelope(
            governed_id=governed_id,
            status="SUCCESS" if policy_decision != PolicyDecision.BLOCK else "BLOCKED",
            formatted_content=formatted_content,
            original_format="MARKDOWN",
            redactions=redaction_records,
            metadata=metadata,
            policy_decision=policy_decision,
            explanation=policy_explanation,
        )
