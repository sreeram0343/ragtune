"""
RAGTUNE Enterprise Text-to-SQL Engine - Domain Models & Schemas
Defines database metadata, SQL validation structures, execution telemetry, and structured results.
"""

from typing import Any

from pydantic import BaseModel, Field


class ColumnSchema(BaseModel):
    name: str
    data_type: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    description: str = ""


class TableSchema(BaseModel):
    table_name: str
    columns: list[ColumnSchema] = Field(default_factory=list)
    description: str = ""
    tenant_id: str = "global_tenant"


class SQLValidationResult(BaseModel):
    is_valid: bool
    error_message: str | None = None
    sanitized_sql: str
    statement_type: str = "SELECT"
    row_limit_applied: int = 100
    requires_hitl_approval: bool = False


class SQLExecutionMetrics(BaseModel):
    generation_latency_ms: float = 0.0
    validation_latency_ms: float = 0.0
    execution_latency_ms: float = 0.0
    formatting_latency_ms: float = 0.0
    total_latency_ms: float = 0.0
    rows_returned: int = 0


class StructuredSQLResult(BaseModel):
    natural_query: str
    generated_sql: str
    sanitized_sql: str = ""
    columns: list[str] = Field(default_factory=list)
    rows: list[Any] = Field(default_factory=list)
    row_count: int = 0
    summary_text: str = ""
    error_message: str | None = None
    metrics: SQLExecutionMetrics = Field(default_factory=SQLExecutionMetrics)

    @property
    def success(self) -> bool:
        return self.error_message is None
