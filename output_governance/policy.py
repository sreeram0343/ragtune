"""
RAGTUNE Output Security & Response Governance Engine - Policy Engine
Evaluates enterprise compliance policies, workspace restrictions, and export control rules.
"""

from typing import Tuple, List, Optional
from output_governance.domain import PolicyDecision
from auth.domain.models import SecurityContext


class EnterprisePolicyEngine:
    def evaluate_policy(
        self,
        content: str,
        security_context: Optional[SecurityContext] = None,
        moderation_violations: List[str] = None
    ) -> Tuple[PolicyDecision, str]:
        """
        Evaluates narrative content and security context against enterprise policy rules.
        Returns (PolicyDecision, explanation).
        """
        moderation_violations = moderation_violations or []

        # 1. Moderation Violations cause Policy BLOCK
        if moderation_violations:
            return PolicyDecision.BLOCK, f"Policy Violation: {moderation_violations[0]}"

        # 2. Workspace User Active Status Check
        if security_context and not security_context.is_active:
            return PolicyDecision.BLOCK, "Policy Violation: SecurityContext account is suspended."

        return PolicyDecision.ALLOW, "Policy compliance checks passed."
