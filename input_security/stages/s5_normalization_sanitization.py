"""
RAGTUNE Input Security Pipeline - Stage 5: Request Normalization & XSS Sanitization
Applies NFKC Unicode normalization, strips zero-width spaces, and filters XSS scripts.
"""

import re
import time
import unicodedata
from typing import Any

from input_security.framework.stage import (
    BaseSecurityStage,
    SecurityRequestContainer,
    StageResult,
)

ZERO_WIDTH_CHARS = ["\u200b", "\u200c", "\u200d", "\ufeff", "\u00ad"]
XSS_PATTERNS = [
    r"<script[^>]*>.*?</script>",
    r"javascript\s*:",
    r"onload\s*=",
    r"onerror\s*=",
    r"onclick\s*=",
    r"<iframe[^>]*>",
]


class NormalizationSanitizationStage(BaseSecurityStage):
    def __init__(self):
        super().__init__(
            stage_id=5, stage_name="Request Normalization & XSS Sanitization"
        )
        self.xss_regexes = [
            re.compile(p, re.IGNORECASE | re.DOTALL) for p in XSS_PATTERNS
        ]

    def _sanitize_string(self, text: str) -> str:
        if not text:
            return text

        # 1. NFKC Unicode Normalization
        normalized = unicodedata.normalize("NFKC", text)

        # 2. Strip Zero-Width & Hidden Characters
        for zw in ZERO_WIDTH_CHARS:
            normalized = normalized.replace(zw, "")

        # 3. Filter XSS Payload Patterns
        for regex in self.xss_regexes:
            normalized = regex.sub("", normalized)

        return normalized

    def _sanitize_recursive(self, data: Any) -> Any:
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return {k: self._sanitize_recursive(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_recursive(item) for item in data]
        return data

    def process(self, container: SecurityRequestContainer) -> StageResult:
        t0 = time.time()
        audit_notes = []

        sanitized_payload = self._sanitize_recursive(container.parsed_payload)

        sanitized_query = None
        if container.user_query:
            sanitized_query = self._sanitize_string(container.user_query)
            container.user_query = sanitized_query

        audit_notes.append(
            "NFKC Unicode normalization, zero-width stripping, and XSS filtering applied clean"
        )

        latency = (time.time() - t0) * 1000
        return StageResult(
            stage_id=self.stage_id,
            stage_name=self.stage_name,
            passed=True,
            threat_score=0.0,
            sanitized_payload=sanitized_payload,
            audit_notes=audit_notes,
            execution_time_ms=round(latency, 2),
        )
