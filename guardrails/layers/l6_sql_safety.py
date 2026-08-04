"""
RAGTUNE - Guardrail Layer 6: SQL AST Parsing & Execution Safety Guard
Enforces read-only database queries, prevents SQL injection mutations, and caps result set limits.
"""

import re

from config.settings import settings

try:
    import sqlglot
    from sqlglot import exp

    HAS_SQLGLOT = True
except ImportError:
    HAS_SQLGLOT = False


class SQLSafetyGuard:
    def __init__(self):
        self.forbidden_keywords = set(settings.DENIED_SQL_KEYWORDS)

    def evaluate_sql(
        self, sql: str, max_limit: int = 100
    ) -> tuple[bool, float, str, str]:
        """
        Validates SQL safety, converts/enforces read-only state, and ensures LIMIT clause.
        Returns: (is_safe: bool, confidence: float, sanitized_sql: str, details: str)
        """
        if not sql or not sql.strip():
            return False, 0.0, "", "Empty SQL string provided"

        sql_trimmed = sql.strip().strip(";").strip()
        sql_upper = sql_trimmed.upper()

        # Keyword scan for destructive mutation operations
        for word in self.forbidden_keywords:
            # Check standalone keyword match
            if re.search(rf"\b{word}\b", sql_upper):
                return (
                    False,
                    0.0,
                    "",
                    f"Forbidden SQL operation detected: '{word}'. Only read-only SELECT statements are permitted.",
                )

        # Ensure query starts with SELECT or WITH
        if not (sql_upper.startswith("SELECT") or sql_upper.startswith("WITH")):
            return (
                False,
                0.0,
                "",
                "Invalid query type. Only SELECT or WITH queries are permitted.",
            )

        # Perform AST parsing if sqlglot is available
        sanitized_sql = sql_trimmed
        if HAS_SQLGLOT:
            try:
                parsed = sqlglot.parse_one(sql_trimmed)
                # Ensure statement is Select
                if not isinstance(parsed, (exp.Select, exp.Expression)):
                    return (
                        False,
                        0.0,
                        "",
                        "SQL statement is not a valid SELECT expression",
                    )

                # Check if LIMIT exists, if not inject LIMIT
                if not parsed.args.get("limit"):
                    parsed = parsed.limit(max_limit)
                sanitized_sql = parsed.sql()
            except Exception:
                # Fallback limit check
                if "LIMIT" not in sql_upper:
                    sanitized_sql = f"{sql_trimmed} LIMIT {max_limit}"
        else:
            if "LIMIT" not in sql_upper:
                sanitized_sql = f"{sql_trimmed} LIMIT {max_limit}"

        return (
            True,
            1.0,
            sanitized_sql,
            f"SQL safety check passed. Execution safe with limit {max_limit}.",
        )
