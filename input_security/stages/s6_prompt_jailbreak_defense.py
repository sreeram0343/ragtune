"""
RAGTUNE Input Security Pipeline - Stage 6: Prompt Inspection & Jailbreak Defense
Inspects input prompts for direct/indirect injection, jailbreaks, and system overrides.
"""

import re
import time

from input_security.framework.stage import (
    BaseSecurityStage,
    SecurityRequestContainer,
    SecurityViolationException,
    StageResult,
)

PROMPT_INJECTION_RULES = [
    (r"ignore\s+(all\s+)?previous\s+instructions", 90.0, "Direct prompt override"),
    (r"disregard\s+(all\s+)?prior\s+(rules|prompts)", 90.0, "Prior rules override"),
    (r"system\s+prompt\s+override", 85.0, "System prompt override"),
    (
        r"act\s+as\s+(dan|developer\s+mode|root|unfiltered)",
        95.0,
        "Adversarial roleplay (DAN/Jailbreak)",
    ),
    (r"jailbreak", 80.0, "Explicit jailbreak phrase"),
    (r"bypass\s+(security|guardrails|safety)", 85.0, "Security bypass request"),
    (r"reveal\s+internal\s+prompts?", 75.0, "Prompt leakage attempt"),
    (r"show\s+me\s+your\s+system\s+instructions", 75.0, "System instructions leakage"),
]


class PromptJailbreakDefenseStage(BaseSecurityStage):
    def __init__(self):
        super().__init__(stage_id=6, stage_name="Prompt Inspection & Jailbreak Defense")
        self.compiled_rules = [
            (re.compile(p, re.IGNORECASE), score, desc)
            for p, score, desc in PROMPT_INJECTION_RULES
        ]

    def process(self, container: SecurityRequestContainer) -> StageResult:
        t0 = time.time()
        audit_notes = []
        highest_threat_score = 0.0

        query_text = container.user_query or ""
        if not query_text and "query" in container.parsed_payload:
            query_text = str(container.parsed_payload["query"])

        if query_text:
            for regex, score, desc in self.compiled_rules:
                match = regex.search(query_text)
                if match:
                    highest_threat_score = max(highest_threat_score, score)
                    audit_notes.append(
                        f"Prompt injection threat detected: {desc} ('{match.group(0)}')"
                    )

        if highest_threat_score >= 85.0:
            raise SecurityViolationException(
                message=f"Prompt injection / jailbreak attempt blocked (Threat score: {highest_threat_score})",
                status_code=400,
                stage_name=self.stage_name,
                risk_score=highest_threat_score,
            )

        if highest_threat_score == 0.0:
            audit_notes.append("Prompt inspection clean (No injection patterns found)")

        latency = (time.time() - t0) * 1000
        return StageResult(
            stage_id=self.stage_id,
            stage_name=self.stage_name,
            passed=True,
            threat_score=highest_threat_score,
            sanitized_payload=container.parsed_payload,
            audit_notes=audit_notes,
            execution_time_ms=round(latency, 2),
        )
