"""
RAGTUNE Enterprise Verification & Quality Assurance Engine - Self-RAG Reflector
Evaluates Self-RAG reflection tokens ([IS_SUPPORTED], [IS_RELEVANT], [UTILITY]) for self-critique.
"""

from typing import List, Tuple
from verification.domain import ReflectionToken, VerificationClaim


class SelfRAGReflector:
    def reflect(
        self,
        query: str,
        response_narrative: str,
        claims: List[VerificationClaim]
    ) -> List[ReflectionToken]:
        """
        Computes Self-RAG reflection tokens evaluating answer support, relevance, and utility.
        """
        tokens: List[ReflectionToken] = []

        # 1. [IS_SUPPORTED] Token
        if claims:
            grounded_claims = [c for c in claims if c.is_grounded]
            supp_score = round(len(grounded_claims) / float(len(claims)), 2)
        else:
            supp_score = 1.0

        tokens.append(
            ReflectionToken(
                token_type="[IS_SUPPORTED]",
                score=supp_score,
                rationale=f"{int(supp_score*100)}% of claims are directly supported by source evidence."
            )
        )

        # 2. [IS_RELEVANT] Token
        q_words = set(w.lower() for w in query.split() if len(w) > 3)
        resp_lower = response_narrative.lower()
        if q_words:
            matched_q = sum(1 for w in q_words if w in resp_lower)
            rel_score = round(min(matched_q / float(len(q_words)) + 0.4, 1.0), 2)
        else:
            rel_score = 0.90

        tokens.append(
            ReflectionToken(
                token_type="[IS_RELEVANT]",
                score=rel_score,
                rationale=f"Response directly addresses query objectives (Relevance: {rel_score})."
            )
        )

        # 3. [UTILITY] Token
        util_score = round((supp_score + rel_score) / 2.0, 2)
        tokens.append(
            ReflectionToken(
                token_type="[UTILITY]",
                score=util_score,
                rationale=f"Enterprise answer utility score calibrated at {util_score}."
            )
        )

        return tokens
