"""
RAGTUNE - Guardrail Layer 7: Hallucination & Groundedness Citation Verifier
Verifies response factual alignment and citation grounding against source evidence.
"""

from typing import Tuple, List, Dict
import re


class GroundednessGuard:
    def evaluate_groundedness(
        self, response: str, evidence_chunks: List[str], threshold: float = 0.6
    ) -> Tuple[bool, float, str, Dict[str, float]]:
        """
        Evaluates factual groundedness of response against retrieved evidence chunks.
        Returns: (is_grounded: bool, score: float, details: str, metrics: dict)
        """
        if not response or not response.strip():
            return True, 1.0, "Empty response", {"citation_overlap": 1.0, "sentence_groundedness": 1.0}

        if not evidence_chunks:
            # If query required no evidence chunks (e.g., system metadata/status), return default pass with low confidence
            return True, 0.7, "No external evidence chunks provided to evaluate against", {"citation_overlap": 0.7, "sentence_groundedness": 0.7}

        evidence_text = " ".join(evidence_chunks).lower()
        evidence_words = set(re.findall(r"\w+", evidence_text))

        sentences = [s.strip() for s in re.split(r"[.!?]", response) if len(s.strip()) > 10]
        if not sentences:
            return True, 1.0, "Short response auto-grounded", {"citation_overlap": 1.0, "sentence_groundedness": 1.0}

        grounded_sentences = 0
        sentence_scores = []

        for sentence in sentences:
            words = set(re.findall(r"\w+", sentence.lower()))
            # Remove common stop words
            content_words = {w for w in words if len(w) > 3}
            if not content_words:
                grounded_sentences += 1
                sentence_scores.append(1.0)
                continue

            overlap = content_words.intersection(evidence_words)
            score = len(overlap) / len(content_words)
            sentence_scores.append(score)
            if score >= 0.3:
                grounded_sentences += 1

        overall_score = sum(sentence_scores) / len(sentence_scores) if sentence_scores else 1.0
        sentence_grounded_ratio = grounded_sentences / len(sentences)

        final_groundedness = (overall_score * 0.6) + (sentence_grounded_ratio * 0.4)
        is_safe = final_groundedness >= threshold

        details = (
            f"Groundedness Score: {final_groundedness:.2f} (Threshold: {threshold}). "
            f"{grounded_sentences}/{len(sentences)} response sentences directly verified in evidence."
        )

        return (
            is_safe,
            float(final_groundedness),
            details,
            {
                "citation_overlap": float(overall_score),
                "sentence_groundedness": float(sentence_grounded_ratio),
                "final_score": float(final_groundedness)
            }
        )
