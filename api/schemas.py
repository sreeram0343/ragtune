"""
RAGTUNE - API Request & Response Schemas
Pydantic v2 data transfer models for REST API endpoints.
"""

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(
        ...,
        description="Natural language enterprise query",
        json_schema_extra={"example": "What were top sales in Q3?"},
    )
    role: str | None = Field(
        "ANALYST",
        description="User security role",
        json_schema_extra={"example": "ANALYST"},
    )
    tenant_id: str | None = Field(
        "tenant_enterprise_default", description="Tenant ID context"
    )
    bypass_cache: bool | None = Field(False, description="Bypass cache lookup")


class QueryResponse(BaseModel):
    query: str = Field(..., description="Original natural language query")
    intent_route: str = Field(..., description="Determined intent routing path")
    response: str = Field(..., description="Synthesized response narrative")
    overall_confidence: float = Field(..., description="Groundedness & confidence score between 0.0 and 1.0")
    execution_time_ms: float = Field(..., description="Total execution latency in milliseconds")
    cache_hit: bool = Field(..., description="Whether response was served from cache")
    hitl_flagged: bool = Field(..., description="Whether query was flagged for HITL review")
    hitl_ticket_id: str | None = Field(None, description="HITL ticket ID if flagged")
    hitl_reason: str | None = Field(None, description="Reason for HITL flagging")
    generated_sql: str | None = Field(None, description="Generated SQL statement if applicable")
    sql_rows: list[dict[str, Any]] = Field(default_factory=list, description="SQL query tabular result rows")
    sql_columns: list[str] = Field(default_factory=list, description="SQL result column headers")
    retrieved_chunks: list[dict[str, Any]] = Field(default_factory=list, description="Retrieved vector document chunks")
    guardrail_matrix: list[dict[str, Any]] = Field(default_factory=list, description="9-layer guardrail evaluation metrics")
    trace_id: str | None = Field(None, description="XAI trace identifier for execution auditing")



class IngestTextRequest(BaseModel):
    text: str = Field(..., description="Raw text content to ingest")
    title: str = Field("Enterprise Document", description="Document title")
    doc_id: str | None = Field(None, description="Optional custom document ID")
    metadata: dict[str, Any] | None = Field(default_factory=dict)


class IngestResponse(BaseModel):
    success: bool
    doc_id: str
    title: str
    chunks_created: int
    message: str


class HITLActionRequest(BaseModel):
    ticket_id: str = Field(..., description="HITL ticket identifier")
    action: str = Field(..., description="APPROVE or REJECT")
    operator_id: str = Field("operator_admin", description="ID of reviewing operator")
    operator_notes: str | None = Field(None, description="Review notes")
    modified_sql: str | None = Field(None, description="Optional edited SQL")


class HITLActionResponse(BaseModel):
    success: bool
    message: str
    ticket_id: str
    status: str


class DocumentItem(BaseModel):
    doc_id: str
    title: str
    chunks_count: int
    sample_text: str


class DocumentListResponse(BaseModel):
    total_documents: int
    total_chunks: int
    documents: list[DocumentItem]


class DocumentDeleteResponse(BaseModel):
    success: bool
    doc_id: str
    chunks_removed: int
    message: str


class ExportRequest(BaseModel):
    export_format: str = Field(
        "json", description="Export format: 'json', 'csv', or 'markdown'"
    )
    query_response: QueryResponse


class ExportResponse(BaseModel):
    filename: str
    export_format: str
    content_type: str
    content: str
