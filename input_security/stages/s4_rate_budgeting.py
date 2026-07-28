"""
RAGTUNE Input Security Pipeline - Stage 4: Rate Limiting & Token Budgeting
Enforces request velocity rate limits and caps input token budgets to prevent model abuse.
"""

import time
from typing import Dict, List
from input_security.framework.stage import (
    BaseSecurityStage, StageResult, SecurityRequestContainer, SecurityViolationException
)

MAX_REQUESTS_PER_MINUTE = 60
MAX_INPUT_TOKEN_BUDGET = 4000  # max tokens per query


class RateBudgetingStage(BaseSecurityStage):
    def __init__(self):
        super().__init__(stage_id=4, stage_name="Rate Limiting & Token Budgeting")
        self._user_velocity: Dict[str, List[float]] = {}

    def _estimate_token_count(self, text: str) -> int:
        """Estimates token count (~1 token per 4 characters or word count * 1.3)."""
        if not text:
            return 0
        words = text.split()
        return max(len(words), int(len(text) / 4))

    def process(self, container: SecurityRequestContainer) -> StageResult:
        t0 = time.time()
        audit_notes = []
        now = time.time()

        # 1. Rate Limiting Velocity Check
        caller_id = (container.user_context.user_id if container.user_context else container.client_ip) or "anonymous"
        timestamps = self._user_velocity.get(caller_id, [])
        # Filter timestamps outside 60s window
        timestamps = [t for t in timestamps if now - t < 60.0]
        timestamps.append(now)
        self._user_velocity[caller_id] = timestamps

        if len(timestamps) > MAX_REQUESTS_PER_MINUTE:
            raise SecurityViolationException(
                message=f"Rate limit exceeded: Caller '{caller_id}' exceeded {MAX_REQUESTS_PER_MINUTE} requests/minute limit",
                status_code=429,
                stage_name=self.stage_name,
                risk_score=80.0
            )

        audit_notes.append(f"Request rate OK ({len(timestamps)}/60 req/min)")

        # 2. Token Budgeting Check
        query_text = container.user_query or ""
        if not query_text and "query" in container.parsed_payload:
            query_text = str(container.parsed_payload["query"])

        est_tokens = self._estimate_token_count(query_text)
        if est_tokens > MAX_INPUT_TOKEN_BUDGET:
            raise SecurityViolationException(
                message=f"Token budget exceeded: Estimated input ({est_tokens} tokens) exceeds maximum limit ({MAX_INPUT_TOKEN_BUDGET} tokens)",
                status_code=429,
                stage_name=self.stage_name,
                risk_score=75.0
            )

        audit_notes.append(f"Token budget OK (Estimated tokens: {est_tokens}/{MAX_INPUT_TOKEN_BUDGET})")

        latency = (time.time() - t0) * 1000
        return StageResult(
            stage_id=self.stage_id,
            stage_name=self.stage_name,
            passed=True,
            threat_score=0.0,
            sanitized_payload=container.parsed_payload,
            audit_notes=audit_notes,
            execution_time_ms=round(latency, 2)
        )
