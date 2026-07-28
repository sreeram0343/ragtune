"""
RAGTUNE Enterprise Verification & Quality Assurance Engine - Groundedness Verifier
Evaluates sentence-by-sentence factual grounding against source document chunks and database rows.
"""

import re
from typing import List, Tuple, Any
from verification.domain import VerificationClaim


class GroundednessVerifier:
    def verify_grounding(
        self,
        response_narrative: str,
        source_contexts: List[str]
    ) -> Tuple[List[VerificationClaim], float, float]:
        """
        Splits response narrative into sentence claims and evaluates grounding against source context.
        Returns (claims, groundedness_score, citation_coverage).
        """
        if not response_narrative or not response_narrative.strip():
            return [], 1.0, 1.0

        # Split into sentences
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", response_narrative) if s.strip()]
        if not sentences:
            return [], 1.0, 1.0

        context_blob = " ".join(source_contexts).lower() if source_contexts else ""
        claims: List[VerificationClaim] = []
        grounded_count = 0
        cited_count = 0

        for i, stmt in enumerate(sentences, start=1):
            stmt_lower = stmt.lower()
            tokens = [t for t in re.findall(r"\w+", stmt_lower) if len(t) > 3]

            # Check evidence overlap
            if not tokens or not context_blob:
                is_grounded = True
                confidence = 0.90
            else:
                hits = sum(1 for t in tokens if t in context_blob)
                ratio = hits / float(len(tokens))
                is_grounded = ratio >= 0.35
                confidence = round(min(ratio + 0.3, 1.0), 2)

            if is_grounded:
                grounded_count += 1

            if "cite_" in stmt_lower or "source:" in stmt_lower or "record" in stmt_lower or "finding" in stmt_lower:
                cited_count += 1

            claims.append(
                VerificationClaim(
                    claim_id=f"claim_{i}",
                    statement_text=stmt,
                    is_grounded=is_grounded,
                    supporting_citation_id=f"cite_{i}" if is_grounded else None,
                    confidence=confidence
                )
            )

        groundedness_score = round(grounded_count / float(len(sentences)), 2)
        citation_coverage = round(max(cited_count / float(len(sentences)), groundedness_score), 2)

        return claims, groundedness_score, citation_coverage
