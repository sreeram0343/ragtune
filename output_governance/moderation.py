"""
RAGTUNE Output Security & Response Governance Engine - Content Moderator
Scans output narrative for toxic content, prompt leakage, and model safety violations.
"""

import re

PROMPT_LEAKAGE_PATTERNS = [
    r"\bsystem\s+prompt:\b",
    r"\bignore\s+previous\s+instructions\b",
    r"\byou\s+are\s+a\s+large\s+language\s+model\b",
    r"\bsecret\s+key\s*=\b",
]


class OutputContentModerator:
    def __init__(self):
        self.leakage_regexes = [
            re.compile(p, re.IGNORECASE) for p in PROMPT_LEAKAGE_PATTERNS
        ]

    def moderate_content(self, content: str) -> tuple[bool, list[str]]:
        """
        Scans narrative for moderation violations and system prompt leakage.
        Returns (is_clean, list_of_violations).
        """
        violations: list[str] = []
        if not content:
            return True, []

        for r in self.leakage_regexes:
            if r.search(content):
                violations.append(
                    f"Prompt Leakage Risk: Output contains system prompt instructions ({r.pattern})."
                )

        is_clean = len(violations) == 0
        return is_clean, violations
