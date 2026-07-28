"""
RAGTUNE - Text-to-SQL Engine
Generates, validates, repairs, and executes database queries from natural language.
"""

import re
from typing import Dict, Any, List, Tuple, Optional
from pydantic import BaseModel
from storage.db_connector import DBConnector
from guardrails.layers.l6_sql_safety import SQLSafetyGuard


class SQLGenerationResult(BaseModel):
    success: bool
    generated_sql: str
    sanitized_sql: str
    rows: List[Dict[str, Any]] = []
    columns: List[str] = []
    row_count: int = 0
    explanation: str = ""
    error_message: Optional[str] = None
    repair_attempted: bool = False


class Text2SQLEngine:
    def __init__(self, db_connector: DBConnector):
        self.db = db_connector
        self.sql_guard = SQLSafetyGuard()

    def generate_sql_heuristic(self, query: str, schema_summary: str) -> str:
        """
        Synthesizes SQL query based on natural language intent and schema metadata.
        """
        q_lower = query.lower()
        
        # Check table matches
        schema_metadata = self.db.get_schema_metadata()
        matched_table = None
        for t in schema_metadata:
            if t.table_name.lower() in q_lower or t.table_name.lower()[:-1] in q_lower:
                matched_table = t.table_name
                break

        if not matched_table and schema_metadata:
            # Fallback to first table if none explicitly mentioned
            matched_table = schema_metadata[0].table_name

        if not matched_table:
            return "SELECT 1 AS default_query;"

        # Count intent
        if "count" in q_lower or "how many" in q_lower or "total number" in q_lower:
            return f"SELECT COUNT(*) AS total_count FROM {matched_table};"

        # Revenue / Sales sum intent
        if ("revenue" in q_lower or "sales" in q_lower or "amount" in q_lower or "total" in q_lower):
            # Check for revenue/amount column
            table_info = next((t for t in schema_metadata if t.table_name == matched_table), None)
            num_col = None
            if table_info:
                for c in table_info.columns:
                    if any(k in c.name.lower() for k in ["amount", "revenue", "price", "val", "total", "cost"]):
                        num_col = c.name
                        break
            if num_col:
                return f"SELECT SUM({num_col}) AS total_sum FROM {matched_table};"

        # General SELECT * intent with default ordering if timestamp column exists
        table_info = next((t for t in schema_metadata if t.table_name == matched_table), None)
        date_col = None
        if table_info:
            for c in table_info.columns:
                if any(k in c.name.lower() for k in ["date", "time", "created", "timestamp"]):
                    date_col = c.name
                    break

        if date_col:
            return f"SELECT * FROM {matched_table} ORDER BY {date_col} DESC LIMIT 20;"

        return f"SELECT * FROM {matched_table} LIMIT 20;"

    def process_query(self, query: str) -> SQLGenerationResult:
        """
        Generates SQL, validates safety, executes query, and performs auto-repair if needed.
        """
        schema_summary = self.db.get_schema_summary_str()
        generated_sql = self.generate_sql_heuristic(query, schema_summary)

        # Validate SQL Safety via Guardrail
        is_safe, _, sanitized_sql, safety_details = self.sql_guard.evaluate_sql(generated_sql)
        if not is_safe:
            return SQLGenerationResult(
                success=False,
                generated_sql=generated_sql,
                sanitized_sql="",
                explanation=f"SQL safety violation: {safety_details}",
                error_message=safety_details
            )

        # Execute safe SQL
        success, rows, cols, exec_details = self.db.execute_read_query(sanitized_sql)

        # Attempt Automated Query Repair if query failed
        repair_attempted = False
        if not success:
            repair_attempted = True
            # Simple fallback repair: select top 10 from primary table
            schema_meta = self.db.get_schema_metadata()
            if schema_meta:
                fallback_table = schema_meta[0].table_name
                sanitized_sql = f"SELECT * FROM {fallback_table} LIMIT 10;"
                success, rows, cols, exec_details = self.db.execute_read_query(sanitized_sql)

        explanation = (
            f"Generated and executed query on database. {exec_details}"
        )

        return SQLGenerationResult(
            success=success,
            generated_sql=generated_sql,
            sanitized_sql=sanitized_sql,
            rows=rows,
            columns=cols,
            row_count=len(rows),
            explanation=explanation,
            error_message=None if success else exec_details,
            repair_attempted=repair_attempted
        )
