"""
RAGTUNE Enterprise Text-to-SQL Engine - Result Interpreter & Formatter
Packages raw database cursor rows into structured data tables, statistical summaries, and citations.
"""

from typing import Any

from text2sql.domain import SQLExecutionMetrics, StructuredSQLResult


class ResultInterpreter:
    def format_results(
        self,
        query: str,
        sql: str,
        columns: list[str],
        rows: list[list[Any]],
        metrics: SQLExecutionMetrics,
    ) -> StructuredSQLResult:
        """
        Formats database cursor rows into structured tabular data and summary statistics.
        """
        row_count = len(rows)
        col_summary = ", ".join(columns) if columns else "none"

        summary = (
            f"Structured database query executed successfully returning {row_count} row(s). "
            f"Fields returned: [{col_summary}]."
        )

        metrics.rows_returned = row_count

        return StructuredSQLResult(
            natural_query=query,
            generated_sql=sql,
            columns=columns,
            rows=rows,
            row_count=row_count,
            summary_text=summary,
            metrics=metrics,
        )
