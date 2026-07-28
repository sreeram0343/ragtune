"""
RAGTUNE Enterprise Text-to-SQL Engine - Master Engine Harness
Exposes unified execute_structured_query API orchestrating schema discovery, SQL generation, validation, execution, and formatting.
"""

import time
from typing import Optional
from input_security.framework.stage import EnrichedSecurityRequest
from text2sql.domain import StructuredSQLResult, SQLExecutionMetrics
from text2sql.schema import SchemaIntrospector
from text2sql.generator import SQLGenerator
from text2sql.validator import SQLValidator
from text2sql.execution import SQLExecutionEngine
from text2sql.interpreter import ResultInterpreter


class EnterpriseText2SQLEngine:
    def __init__(
        self,
        schema_introspector: Optional[SchemaIntrospector] = None,
        db_path: str = "demo_data/enterprise_db.sqlite"
    ):
        self.schema_introspector = schema_introspector if schema_introspector else SchemaIntrospector()
        self.generator = SQLGenerator()
        self.validator = SQLValidator(max_row_limit=100)
        self.execution_engine = SQLExecutionEngine(db_path=db_path)
        self.interpreter = ResultInterpreter()

    def execute_structured_query(
        self,
        security_request: EnrichedSecurityRequest
    ) -> StructuredSQLResult:
        """
        Main Structured Query API:
        Translates natural language request into safe read-only SQL, executes it, and packages tabular results.
        """
        t0 = time.time()
        query = security_request.sanitized_query
        sec_ctx = security_request.security_context

        # 1. Schema Discovery & Table Matching
        t_gen_start = time.time()
        matched_tables = self.schema_introspector.match_tables_for_query(query)
        generated_sql, params = self.generator.generate_sql(query, matched_tables)
        t_gen_end = time.time()

        # 2. Multi-Stage SQL Validation & AST Security Check
        t_val_start = time.time()
        val_result = self.validator.validate_sql(generated_sql, security_context=sec_ctx)
        t_val_end = time.time()

        if not val_result.is_valid:
            return StructuredSQLResult(
                natural_query=query,
                generated_sql=generated_sql,
                columns=["error"],
                rows=[[val_result.error_message]],
                row_count=0,
                summary_text=f"SQL Validation Failed: {val_result.error_message}"
            )

        # 3. Read-Only Execution Engine
        t_exec_start = time.time()
        columns, rows = self.execution_engine.execute_read_only_query(
            sql=val_result.sanitized_sql,
            params=params
        )
        t_exec_end = time.time()

        # 4. Result Formatting & Packaging
        t_fmt_start = time.time()
        metrics = SQLExecutionMetrics(
            generation_latency_ms=round((t_gen_end - t_gen_start) * 1000.0, 2),
            validation_latency_ms=round((t_val_end - t_val_start) * 1000.0, 2),
            execution_latency_ms=round((t_exec_end - t_exec_start) * 1000.0, 2),
            total_latency_ms=round((time.time() - t0) * 1000.0, 2)
        )

        result = self.interpreter.format_results(
            query=query,
            sql=val_result.sanitized_sql,
            columns=columns,
            rows=rows,
            metrics=metrics
        )
        t_fmt_end = time.time()
        result.metrics.formatting_latency_ms = round((t_fmt_end - t_fmt_start) * 1000.0, 2)

        return result
