"""
RAGTUNE - Guardrail Layer 9: Confidential Data & System Prompt Leakage Scanner
Scans output content to prevent leakage of credentials, system prompts, or enterprise secrets.
"""

import re
from typing import Tuple


SECRET_PATTERNS = [
    r"api[_-]?key\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}['\"]?",
    r"password\s*[:=]\s*['\"]?\S+['\"]?",
    r"ragtune-secret-key",
    r"BEGIN\s+PRIVATE\s+KEY",
    r"DATABASE_URL\s*=",
    r"System\s+Instructions:\s*You\s+are",
    r"INTERNAL_PROMPT_SECRET"
]


class DataLeakageGuard:
    def __init__(self):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in SECRET_PATTERNS]

    def evaluate(self, content: str) -> Tuple[bool, float, str]:
        """
        Evaluates generated output to ensure no system secrets or internal prompts leak.
        Returns: (is_clean: bool, score: float, details: str)
        """
        if not content:
            return True, 1.0, "Empty content"

        for pattern in self.compiled_patterns:
            match = pattern.search(content)
            if match:
                return (
                    False,
                    0.0,
                    f"Data leakage guard triggered. Output contains confidential credential or system pattern: '{match.group(0)[:20]}...'"
                )

        return True, 1.0, "Confidential data leakage check passed clean"
