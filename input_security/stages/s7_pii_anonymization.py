"""
RAGTUNE Input Security Pipeline - Stage 7: PII / PHI Detection & Anonymization
Detects and dynamically redacts sensitive PII elements in request inputs.
"""

import time
from typing import Dict, Any, List
from input_security.framework.stage import BaseSecurityStage, StageResult, SecurityRequestContainer
from guardrails.layers.l2_pii_masking import PIIMaskingGuard


class PIIAnonymizationStage(BaseSecurityStage):
    def __init__(self):
        super().__init__(stage_id=7, stage_name="PII & PHI Detection & Anonymization")
        self.pii_guard = PIIMaskingGuard()

    def _mask_value_recursive(self, data: Any, audit_notes: List[str]) -> Any:
        if isinstance(data, str):
            masked, detections = self.pii_guard.process(data)
            if detections:
                types_str = ", ".join(d["type"] for d in detections)
                audit_notes.append(f"Redacted {len(detections)} PII item(s): {types_str}")
            return masked
        elif isinstance(data, dict):
            return {k: self._mask_value_recursive(v, audit_notes) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._mask_value_recursive(item, audit_notes) for item in data]
        return data

    def process(self, container: SecurityRequestContainer) -> StageResult:
        t0 = time.time()
        audit_notes: List[str] = []

        sanitized_payload = self._mask_value_recursive(container.parsed_payload, audit_notes)

        if container.user_query:
            masked_query, detections = self.pii_guard.process(container.user_query)
            container.user_query = masked_query
            if detections and not audit_notes:
                audit_notes.append(f"Redacted {len(detections)} PII item(s) in query")

        if not audit_notes:
            audit_notes.append("No sensitive PII elements detected in payload")

        latency = (time.time() - t0) * 1000
        return StageResult(
            stage_id=self.stage_id,
            stage_name=self.stage_name,
            passed=True,
            threat_score=0.0,
            sanitized_payload=sanitized_payload,
            audit_notes=audit_notes,
            execution_time_ms=round(latency, 2)
        )
