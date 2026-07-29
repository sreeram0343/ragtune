"""
RAGTUNE Output Security & Response Governance Engine - Sensitive Data Redactor
Detects and redacts PII, API keys, passwords, and secrets with permission-aware visibility.
"""

import re
from typing import Tuple, List, Optional
from output_governance.domain import RedactionRecord
from auth.domain.models import SecurityContext

# Sensitive data patterns
EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
PHONE_PATTERN = r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"
SSN_PATTERN = r"\b\d{3}-\d{2}-\d{4}\b"
API_KEY_PATTERN = r"\b(?:sk-[A-Za-z0-9_\-]{20,}|AKIA[0-9A-Z]{16})\b"


class SensitiveDataRedactor:
    def sanitize_output(
        self,
        content: str,
        security_context: Optional[SecurityContext] = None
    ) -> Tuple[str, List[RedactionRecord]]:
        """
        Scans narrative for PII and secrets, applying permission-aware masking.
        Returns (sanitized_content, redaction_records).
        """
        if not content:
            return "", []

        user_perms = security_context.permissions if security_context and security_context.permissions else set()
        # Admin bypass role check
        if "security:admin" in user_perms:
            return content, []

        sanitized = content
        records: List[RedactionRecord] = []

        # 1. API Keys Redaction
        api_matches = list(re.finditer(API_KEY_PATTERN, sanitized))
        if api_matches:
            sanitized = re.sub(API_KEY_PATTERN, "[REDACTED_API_KEY]", sanitized)
            records.append(
                RedactionRecord(
                    field_name="api_key",
                    data_type="API_KEY",
                    masked_placeholder="[REDACTED_API_KEY]",
                    count=len(api_matches)
                )
            )

        # 2. SSN Redaction
        ssn_matches = list(re.finditer(SSN_PATTERN, sanitized))
        if ssn_matches:
            sanitized = re.sub(SSN_PATTERN, "[REDACTED_SSN]", sanitized)
            records.append(
                RedactionRecord(
                    field_name="ssn",
                    data_type="SSN",
                    masked_placeholder="[REDACTED_SSN]",
                    count=len(ssn_matches)
                )
            )

        # 3. Email Redaction (unless hr:admin)
        if "hr:admin" not in user_perms:
            email_matches = list(re.finditer(EMAIL_PATTERN, sanitized))
            if email_matches:
                sanitized = re.sub(EMAIL_PATTERN, "[REDACTED_EMAIL]", sanitized)
                records.append(
                    RedactionRecord(
                        field_name="email",
                        data_type="EMAIL",
                        masked_placeholder="[REDACTED_EMAIL]",
                        count=len(email_matches)
                    )
                )

        return sanitized, records
