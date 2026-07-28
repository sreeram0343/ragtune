"""
RAGTUNE - Guardrail Layer 3: Domain & Topic Scope Boundary Guard
Ensures user queries remain strictly within enterprise domain boundaries.
"""

from typing import Tuple


OFF_TOPIC_KEYWORDS = [
    "recipe", "cook", "bake", "ingredient",
    "video game", "minecraft", "fortnite", "playstation", "xbox",
    "movie review", "celebrity gossip", "horoscope", "astrology",
    "sports score", "nfl", "nba", "football match",
    "joke", "riddle", "tell me a story"
]

ENTERPRISE_KEYWORDS = [
    "sql", "table", "data", "customer", "order", "contract",
    "sla", "revenue", "sales", "document", "policy", "report",
    "metric", "user", "account", "database", "analytics", "churn",
    "compliance", "reimbursement", "leave", "employee", "product"
]


class DomainBoundaryGuard:
    def evaluate(self, query: str) -> Tuple[bool, float, str]:
        """
        Evaluates query for enterprise domain relevance.
        Returns: (is_relevant: bool, score: float, details: str)
        """
        if not query:
            return True, 1.0, "Empty query"

        query_lower = query.lower()

        # Check explicit off-topic triggers
        for kw in OFF_TOPIC_KEYWORDS:
            if f" {kw} " in f" {query_lower} " or query_lower.startswith(kw):
                return False, 0.2, f"Out-of-scope domain topic detected: '{kw}'"

        # Match enterprise relevance indicators
        enterprise_matches = [kw for kw in ENTERPRISE_KEYWORDS if kw in query_lower]
        if enterprise_matches or len(query.split()) > 3:
            return True, 0.95, f"Query aligns with enterprise domain (matched: {', '.join(enterprise_matches[:3]) or 'general query'})"

        return True, 0.8, "Query accepted under domain boundary evaluation"
