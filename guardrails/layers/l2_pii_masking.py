"""
RAGTUNE - Guardrail Layer 2: PII / PHI Detection & Anonymization Engine
Detects and dynamically masks sensitive personally identifiable information.
"""

import re
from typing import Tuple, List, Dict
from config.settings import settings


PII_REGEX_MAP = {
    "EMAIL": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "PHONE": r"\(?\b[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}\b",
    "SSN": r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b",
    "CREDIT_CARD": r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",
    "IP_ADDRESS": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
}


class PIIMaskingGuard:
    def __init__(self):
        self.compiled_map = {
            pii_type: re.compile(pattern) 
            for pii_type, pattern in PII_REGEX_MAP.items()
        }

    def process(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Masks PII elements in text.
        Returns: (anonymized_text, list_of_detections)
        """
        if not text:
            return text, []

        masked_text = text
        detections = []

        for pii_type, regex in self.compiled_map.items():
            matches = list(regex.finditer(masked_text))
            for match in matches:
                val = match.group(0)
                mask_token = f"[{pii_type}_PROTECTED]"
                detections.append({"type": pii_type, "original": val, "replacement": mask_token})

            masked_text = regex.sub(f"[{pii_type}_PROTECTED]", masked_text)

        return masked_text, detections

    def evaluate(self, query: str) -> Tuple[bool, float, str, str]:
        """
        Evaluates input query for PII presence and returns masked text.
        Returns: (is_clean: bool, confidence: float, masked_text: str, details: str)
        """
        masked_text, detections = self.process(query)
        if detections:
            details = f"Detected and anonymized {len(detections)} PII item(s): " + ", ".join(d["type"] for d in detections)
            return True, 0.9, masked_text, details
        
        return True, 1.0, query, "No sensitive PII detected"
