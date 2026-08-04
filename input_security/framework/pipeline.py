"""
RAGTUNE Input Security Pipeline - Master Orchestrator
Executes all 8 security stages in defense-in-depth sequence.
"""


from auth.storage.auth_db import AuthDatabaseRepository
from input_security.framework.stage import (
    BaseSecurityStage,
    EnrichedSecurityRequest,
    SecurityRequestContainer,
    StageResult,
)
from input_security.stages.s1_payload_validation import PayloadValidationStage
from input_security.stages.s2_auth_verification import AuthVerificationStage
from input_security.stages.s3_rbac_authorization import RBACAuthorizationStage
from input_security.stages.s4_rate_budgeting import RateBudgetingStage
from input_security.stages.s5_normalization_sanitization import (
    NormalizationSanitizationStage,
)
from input_security.stages.s6_prompt_jailbreak_defense import (
    PromptJailbreakDefenseStage,
)
from input_security.stages.s7_pii_anonymization import PIIAnonymizationStage
from input_security.stages.s8_risk_scoring_enrichment import RiskScoringEnrichmentStage


class InputSecurityPipeline:
    def __init__(self, db_repo: AuthDatabaseRepository):
        self.s1_payload = PayloadValidationStage()
        self.s2_auth = AuthVerificationStage(db_repo)
        self.s3_rbac = RBACAuthorizationStage()
        self.s4_rate = RateBudgetingStage()
        self.s5_normalization = NormalizationSanitizationStage()
        self.s6_jailbreak = PromptJailbreakDefenseStage()
        self.s7_pii = PIIAnonymizationStage()
        self.s8_enrichment = RiskScoringEnrichmentStage()

        self.stages: list[BaseSecurityStage] = [
            self.s1_payload,
            self.s2_auth,
            self.s3_rbac,
            self.s4_rate,
            self.s5_normalization,
            self.s6_jailbreak,
            self.s7_pii,
        ]

    def process_request(
        self, container: SecurityRequestContainer
    ) -> EnrichedSecurityRequest:
        """
        Executes sequential 8-stage Defense-in-Depth inspection pipeline.
        Returns: EnrichedSecurityRequest cleared for downstream AI orchestration.
        """
        evaluations: list[StageResult] = []

        # Execute Stages 1 through 7 sequentially
        for stage in self.stages:
            res = stage.process(container)
            evaluations.append(res)
            # Update container parsed payload with stage sanitized payload
            if res.sanitized_payload:
                container.parsed_payload = res.sanitized_payload

        # Execute Stage 8 (Risk Scoring & Context Enrichment)
        enriched_request = self.s8_enrichment.process_enrichment(container, evaluations)
        return enriched_request
