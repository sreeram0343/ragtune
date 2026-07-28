"""
RAGTUNE - Guardrail Layer 1: Prompt Injection & Adversarial Payload Defense
Scans input queries for injection attacks, system overrides, and jailbreak attempts.
"""

import re
from typing import Tuple
from config.settings import settings


INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?prior\s+(rules|prompts)",
    r"system\s+prompt\s+override",
    r"act\s+as\s+(dan|developer\s+mode|root)",
    r"jailbreak",
    r"bypass\s+(security|guardrails|safety)",
    r"reveal\s+internal\s+prompts?",
    r"show\s+me\s+your\s+system\s+instructions",
    r"sudo\s+",
    r"drop\s+database",
    r"<script>",
]


class InjectionGuard:
    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

    def evaluate(self, query: str) -> Tuple[bool, float, str]:
        """
        Evaluates input query for prompt injection.
        Returns: (is_safe: bool, score: float, details: str)
        """
        if not query or not query.strip():
            return True, 1.0, "Empty input query"

        for pattern in self.patterns:
            match = pattern.search(query)
            if match:
                return (
                    False,
                    0.0,
                    f"Prompt injection pattern detected: '{match.group(0)}'"
                )

        # Check configured denied patterns
        query_lower = query.lower()
        for denied in settings.DENIED_PROMPT_PATTERNS:
            if denied.lower() in query_lower:
                return (
                    False,
                    0.0,
                    f"Denied adversarial phrase detected: '{denied}'"
                )

        return True, 1.0, "Prompt injection check passed"
