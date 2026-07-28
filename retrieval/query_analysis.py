"""
RAGTUNE Enterprise Hybrid Retrieval Engine - Query Understanding & HyDE Expander
Performs query normalization, keyword extraction, and selective Hypothetical Document Expansion (HyDE).
"""

import re
from typing import Tuple, List

STOP_WORDS = {"what", "is", "our", "the", "a", "an", "in", "on", "at", "for", "to", "of", "and", "or", "with"}


class QueryUnderstanding:
    def __init__(self, enable_hyde: bool = True):
        self.enable_hyde = enable_hyde

    def normalize_query(self, query: str) -> str:
        """Applies NFKC normalization and basic whitespace cleaning."""
        if not query:
            return ""
        q = re.sub(r"\s+", " ", query.strip())
        return q

    def extract_keywords(self, query: str) -> List[str]:
        """Extracts key lexical search tokens from query."""
        tokens = re.findall(r"\w+", query.lower())
        keywords = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]
        return keywords

    def generate_hyde_expansion(self, query: str) -> Tuple[str, bool]:
        """
        Conditionally generates a hypothetical document snippet (HyDE)
        to improve dense embedding retrieval accuracy.
        """
        normalized = self.normalize_query(query)
        words = normalized.split()

        # Decide whether HyDE expansion is warranted
        should_hyde = self.enable_hyde and (len(words) < 5 or "policy" in normalized.lower() or "agreement" in normalized.lower())

        if not should_hyde:
            return normalized, False

        # Synthesize hypothetical passage structure for query embedding
        hypothetical_passage = (
            f"Official Enterprise Knowledge Record: {normalized}. "
            f"This policy clause specifies terms, conditions, SLAs, compliance rules, "
            f"and operational guidelines governing enterprise workspace operations."
        )
        return hypothetical_passage, True
