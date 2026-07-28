"""
RAGTUNE - Guardrail Layer 8: Toxicity, Bias & Harm Safety Filter
Evaluates generated content for toxic phrases, hate speech, and safety violations.
"""

from typing import Tuple


TOXIC_TERMS = [
    "hate", "slur", "discriminate", "violence", "threaten",
    "illegal act", "malware", "exploit", "hack", "bypass security"
]


class ToxicitySafetyGuard:
    def evaluate(self, content: str) -> Tuple[bool, float, str]:
        """
        Evaluates output content for toxicity or safety violations.
        Returns: (is_safe: bool, score: float, details: str)
        """
        if not content:
            return True, 1.0, "Empty content"

        content_lower = content.lower()
        flagged = []

        for term in TOXIC_TERMS:
            if f" {term} " in f" {content_lower} ":
                flagged.append(term)

        if flagged:
            return (
                False,
                0.1,
                f"Toxicity/Safety violation detected. Content contained flagged terminology: {', '.join(flagged)}"
            )

        return True, 1.0, "Toxicity and safety evaluation passed clean"
