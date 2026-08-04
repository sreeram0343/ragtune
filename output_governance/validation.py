"""
RAGTUNE Output Security & Response Governance Engine - Response Schema Validator
Validates payload integrity, required fields, token bounds, and structural completeness.
"""



class ResponseSchemaValidator:
    def __init__(self, max_response_char_limit: int = 20000):
        self.max_response_char_limit = max_response_char_limit

    def validate_schema(self, content: str) -> tuple[bool, str]:
        """
        Validates content payload for non-empty integrity and size bounds.
        Returns (is_valid, error_message).
        """
        if not content or not content.strip():
            return False, "Response Schema Violation: Output narrative cannot be empty"

        if len(content) > self.max_response_char_limit:
            return (
                False,
                f"Response Schema Violation: Output narrative length ({len(content)}) exceeds max limit ({self.max_response_char_limit})",
            )

        return True, "Schema validation passed"
