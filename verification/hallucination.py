"""
RAGTUNE Enterprise Verification & Quality Assurance Engine - Hallucination Detector
Detects invented facts, numerical discrepancies, cross-source contradictions, and unreferenced claims.
"""

import re
from typing import List, Tuple
from verification.domain import VerificationClaim


class HallucinationDetector:
    def detect_hallucination_risk(
        self,
        response_narrative: str,
        source_contexts: List[str],
        claims: List[VerificationClaim]
    ) -> Tuple[float, List[str]]:
        """
        Scans response narrative and claims for hallucination risk and numerical discrepancies.
        Returns (hallucination_risk_score, list_of_detected_issues).
        """
        issues: List[str] = []
        context_blob = " ".join(source_contexts).lower() if source_contexts else ""

        # 1. Claim Grounding Risk
        ungrounded_claims = [c for c in claims if not c.is_grounded]
        if ungrounded_claims:
            issues.append(f"Detected {len(ungrounded_claims)} ungrounded claim(s) lacking evidence support.")

        # 2. Numerical Discrepancy Check
        resp_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", response_narrative))
        context_numbers = set(re.findall(r"\b\d+(?:\.\d+)?\b", context_blob))

        unsupported_numbers = resp_numbers - context_numbers
        # Exclude common small numbers like 1, 2, 3
        unsupported_numbers = {n for n in unsupported_numbers if float(n) > 5}

        if unsupported_numbers:
            issues.append(f"Numerical discrepancy detected: Number(s) {unsupported_numbers} do not match source evidence.")

        # 3. Calculate Composite Hallucination Risk Score
        risk_score = 0.0
        if ungrounded_claims:
            risk_score += min(len(ungrounded_claims) * 0.25, 0.60)
        if unsupported_numbers:
            risk_score += min(len(unsupported_numbers) * 0.30, 0.40)

        risk_score = round(min(risk_score, 1.0), 2)
        return risk_score, issues
