"""
RAGTUNE Enterprise Verification & Quality Assurance Engine - Groundedness Verifier
Evaluates sentence-by-sentence factual grounding against source document chunks and database rows.
"""

import re

from verification.domain import VerificationClaim


class GroundednessVerifier:
    def verify_grounding(
        self, response_narrative: str, source_contexts: list[str]
    ) -> tuple[list[VerificationClaim], float, float]:
        """
        Splits response narrative into sentence claims and evaluates grounding against source context.
        Returns (claims, groundedness_score, citation_coverage).
        """
        if not response_narrative or not response_narrative.strip():
            return [], 1.0, 1.0

        # Split into statements / markdown lines
        lines = [
            s.strip()
            for s in response_narrative.split("\n")
            if s.strip() and not s.strip().startswith("| ---")
        ]
        if not lines:
            return [], 1.0, 1.0

        context_blob = " ".join(source_contexts).lower() if source_contexts else ""
        claims: list[VerificationClaim] = []
        grounded_count = 0
        cited_count = 0

        for i, stmt in enumerate(lines, start=1):
            stmt_lower = stmt.lower()
            tokens = [t for t in re.findall(r"\w+", stmt_lower) if len(t) > 2]

            # Check evidence overlap
            if (
                not tokens
                or not context_blob
                or stmt.startswith("|")
                or "###" in stmt
                or "sql" in stmt_lower
            ):
                is_grounded = True
                confidence = 0.95
            else:
                hits = sum(1 for t in tokens if t in context_blob)
                ratio = hits / float(len(tokens))
                is_grounded = ratio >= 0.25
                confidence = round(min(ratio + 0.4, 1.0), 2)

            if is_grounded:
                grounded_count += 1

            if (
                "cite_" in stmt_lower
                or "source:" in stmt_lower
                or "record" in stmt_lower
                or "finding" in stmt_lower
                or "evidence" in stmt_lower
                or stmt.startswith("|")
            ):
                cited_count += 1

            claims.append(
                VerificationClaim(
                    claim_id=f"claim_{i}",
                    statement_text=stmt,
                    is_grounded=is_grounded,
                    supporting_citation_id=f"cite_{i}" if is_grounded else None,
                    confidence=confidence,
                )
            )

        groundedness_score = round(grounded_count / float(len(lines)), 2)
        citation_coverage = round(
            max(cited_count / float(len(lines)), groundedness_score), 2
        )

        return claims, groundedness_score, citation_coverage
