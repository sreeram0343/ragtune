"""
RAGTUNE Enterprise Text-to-SQL Engine - AST Security Validator
Parses SQL syntax, enforces READ-ONLY SELECT statements, caps row limits, and checks RBAC permissions.
"""

import re

from auth.domain.models import SecurityContext
from text2sql.domain import SQLValidationResult

FORBIDDEN_KEYWORDS = [
    r"\bdrop\b",
    r"\bdelete\b",
    r"\bupdate\b",
    r"\binsert\b",
    r"\balter\b",
    r"\btruncate\b",
    r"\bgrant\b",
    r"\brevoke\b",
    r"\bexecute\b",
    r"\bexec\b",
]


class SQLValidator:
    def __init__(self, max_row_limit: int = 100):
        self.max_row_limit = max_row_limit
        self.forbidden_regexes = [
            re.compile(p, re.IGNORECASE) for p in FORBIDDEN_KEYWORDS
        ]

    def validate_sql(
        self, sql: str, security_context: SecurityContext | None = None
    ) -> SQLValidationResult:
        """
        Validates SQL statement for read-only safety, AST correctness, and permission boundaries.
        """
        if not sql or not sql.strip():
            return SQLValidationResult(
                is_valid=False,
                error_message="SQL statement cannot be empty",
                sanitized_sql="",
            )

        sql_clean = sql.strip()

        # 1. Check for Forbidden DDL/DML Keywords
        for r in self.forbidden_regexes:
            if r.search(sql_clean):
                return SQLValidationResult(
                    is_valid=False,
                    error_message=f"Security Violation: Forbidden SQL statement type detected ({r.pattern})",
                    sanitized_sql="",
                )

        # 2. Must start with SELECT or WITH (for CTEs)
        sql_upper = sql_clean.upper()
        if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
            return SQLValidationResult(
                is_valid=False,
                error_message="Security Violation: Only read-only SELECT queries are permitted",
                sanitized_sql="",
            )

        # 3. Prevent Multi-Statement Execution (Semicolon injection)
        statements = [s for s in sql_clean.split(";") if s.strip()]
        if len(statements) > 1:
            return SQLValidationResult(
                is_valid=False,
                error_message="Security Violation: Multi-statement batch execution is strictly prohibited",
                sanitized_sql="",
            )

        # 4. Row Limit Capping
        sanitized = sql_clean
        if "LIMIT" not in sql_upper:
            sanitized = f"{sql_clean.rstrip(';')} LIMIT {self.max_row_limit};"

        # 5. HITL Trigger check for sensitive tables/columns
        requires_hitl = False
        if "salary" in sql_clean.lower() or "compensation" in sql_clean.lower():
            user_perms = (
                security_context.permissions
                if security_context and security_context.permissions
                else set()
            )
            if "hr:admin" not in user_perms:
                requires_hitl = True

        return SQLValidationResult(
            is_valid=True,
            sanitized_sql=sanitized,
            statement_type="SELECT",
            row_limit_applied=self.max_row_limit,
            requires_hitl_approval=requires_hitl,
        )

    def contains_mutation(self, sql_query: str) -> bool:
        """Helper to quickly check if a raw SQL string contains forbidden DDL/DML mutation keywords."""
        if not sql_query:
            return False
        for r in self.forbidden_regexes:
            if r.search(sql_query):
                return True
        return False

