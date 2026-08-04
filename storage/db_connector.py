"""
RAGTUNE - Database Connector & Schema Introspection Engine
Provides structured database interaction, schema reflection, and safe SQL execution.
"""

import os
from typing import Any

from pydantic import BaseModel
from sqlalchemy import create_engine, inspect, text

from config.settings import settings


class ColumnMetadata(BaseModel):
    name: str
    type: str
    nullable: bool
    primary_key: bool


class TableMetadata(BaseModel):
    table_name: str
    columns: list[ColumnMetadata]
    row_count: int
    sample_rows: list[dict[str, Any]]


class DBConnector:
    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or settings.DATABASE_URL
        # Ensure directory exists for sqlite DB files
        if self.db_url.startswith("sqlite:///"):
            db_path = self.db_url.replace("sqlite:///", "")
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)

        self.engine = create_engine(
            self.db_url,
            echo=False,
            connect_args=(
                {"check_same_thread": False} if "sqlite" in self.db_url else {}
            ),
        )

    def get_schema_metadata(self) -> list[TableMetadata]:
        """
        Inspects connected database and extracts complete schema metadata.
        """
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()
        schema_list: list[TableMetadata] = []

        with self.engine.connect() as conn:
            for t_name in table_names:
                cols = inspector.get_columns(t_name)
                col_metas = [
                    ColumnMetadata(
                        name=c["name"],
                        type=str(c["type"]),
                        nullable=c.get("nullable", True),
                        primary_key=bool(c.get("primary_key", False)),
                    )
                    for c in cols
                ]

                # Row count
                try:
                    count_res = conn.execute(
                        text(f"SELECT COUNT(*) FROM {t_name}")
                    ).scalar()
                    row_count = int(count_res or 0)
                except Exception:
                    row_count = 0

                # Sample rows (up to 3)
                try:
                    sample_res = conn.execute(text(f"SELECT * FROM {t_name} LIMIT 3"))
                    sample_rows = [dict(row._mapping) for row in sample_res]
                except Exception:
                    sample_rows = []

                schema_list.append(
                    TableMetadata(
                        table_name=t_name,
                        columns=col_metas,
                        row_count=row_count,
                        sample_rows=sample_rows,
                    )
                )

        return schema_list

    def get_schema_summary_str(self) -> str:
        """
        Formats schema metadata into a clean text prompt for Text-to-SQL agents.
        """
        schema_list = self.get_schema_metadata()
        summary_lines = []

        for table in schema_list:
            cols_str = ", ".join([f"{c.name} ({c.type})" for c in table.columns])
            summary_lines.append(
                f"Table '{table.table_name}' [{table.row_count} rows]: ({cols_str})"
            )

        return "\n".join(summary_lines)

    def execute_read_query(
        self, sql: str, max_rows: int = 100
    ) -> tuple[bool, list[dict[str, Any]], list[str], str]:
        """
        Executes a safe read-only SQL query.
        Returns: (success: bool, rows: list[dict], column_names: list[str], error_or_details: str)
        """
        if not sql or not sql.strip():
            return False, [], [], "Empty SQL statement"

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                cols = list(result.keys())
                fetched = result.fetchmany(max_rows)
                rows = [dict(row._mapping) for row in fetched]
                return (
                    True,
                    rows,
                    cols,
                    f"Successfully executed query. Returned {len(rows)} row(s).",
                )
        except Exception as e:
            return False, [], [], f"SQL Execution Error: {e!s}"
