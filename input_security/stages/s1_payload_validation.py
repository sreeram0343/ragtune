"""
RAGTUNE Input Security Pipeline - Stage 1: Payload & Schema Validation
Validates request body size (2MB max), JSON structure, and path traversal threats.
"""

import json
import re
import time
from typing import Any

from input_security.framework.stage import (
    BaseSecurityStage,
    SecurityRequestContainer,
    SecurityViolationException,
    StageResult,
)

MAX_PAYLOAD_BYTES = 2 * 1024 * 1024  # 2MB
PATH_TRAVERSAL_PATTERNS = [
    r"\.\.[/\\]",
    r"/etc/passwd",
    r"c:\\windows",
    r"\\system32\\",
    r"file:///",
]


class PayloadValidationStage(BaseSecurityStage):
    def __init__(self):
        super().__init__(stage_id=1, stage_name="Payload & Schema Validation")
        self.traversal_regexes = [
            re.compile(p, re.IGNORECASE) for p in PATH_TRAVERSAL_PATTERNS
        ]

    def process(self, container: SecurityRequestContainer) -> StageResult:
        t0 = time.time()
        audit_notes = []
        threat_score = 0.0

        # 1. Byte Size Verification
        raw_len = len(container.raw_body)
        if raw_len > MAX_PAYLOAD_BYTES:
            raise SecurityViolationException(
                message=f"Payload size ({raw_len} bytes) exceeds maximum permitted limit ({MAX_PAYLOAD_BYTES} bytes)",
                status_code=413,
                stage_name=self.stage_name,
                risk_score=100.0,
            )

        audit_notes.append(f"Payload size OK ({raw_len} bytes)")

        # 2. JSON Structure Parsing (if non-empty body)
        parsed_data: dict[str, Any] = dict(container.parsed_payload)
        if container.raw_body and not parsed_data:
            try:
                parsed_data = json.loads(container.raw_body.decode("utf-8"))
            except Exception as e:
                raise SecurityViolationException(
                    message=f"Malformed JSON payload: {e!s}",
                    status_code=400,
                    stage_name=self.stage_name,
                    risk_score=90.0,
                )

        # 3. Path Traversal Threat Inspection
        payload_str = json.dumps(parsed_data).lower()
        for regex in self.traversal_regexes:
            match = regex.search(payload_str)
            if match:
                threat_score += 40.0
                audit_notes.append(
                    f"Path traversal sequence detected: '{match.group(0)}'"
                )

        if threat_score >= 80.0:
            raise SecurityViolationException(
                message="Critical path traversal attempt detected in payload",
                status_code=400,
                stage_name=self.stage_name,
                risk_score=threat_score,
            )

        latency = (time.time() - t0) * 1000
        return StageResult(
            stage_id=self.stage_id,
            stage_name=self.stage_name,
            passed=True,
            threat_score=threat_score,
            sanitized_payload=parsed_data,
            audit_notes=audit_notes,
            execution_time_ms=round(latency, 2),
        )
