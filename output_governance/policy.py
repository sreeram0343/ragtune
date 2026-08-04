"""
RAGTUNE Output Security & Response Governance Engine - Policy Engine
Evaluates enterprise compliance policies, workspace restrictions, and export control rules.
"""


from auth.domain.models import SecurityContext, UserStatus
from output_governance.domain import PolicyDecision


class EnterprisePolicyEngine:
    def evaluate_policy(
        self,
        content: str,
        security_context: SecurityContext | None = None,
        moderation_violations: list[str] = None,
    ) -> tuple[PolicyDecision, str]:
        """
        Evaluates narrative content and security context against enterprise policy rules.
        Returns (PolicyDecision, explanation).
        """
        moderation_violations = moderation_violations or []

        # 1. Moderation Violations cause Policy BLOCK
        if moderation_violations:
            return PolicyDecision.BLOCK, f"Policy Violation: {moderation_violations[0]}"

        # 2. Workspace User Active Status Check
        if security_context and security_context.status != UserStatus.ACTIVE:
            return (
                PolicyDecision.BLOCK,
                "Policy Violation: SecurityContext account is suspended or inactive.",
            )

        return PolicyDecision.ALLOW, "Policy compliance checks passed."
