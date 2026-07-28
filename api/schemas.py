"""
RAGTUNE - API Request & Response Schemas
Pydantic v2 data transfer models for REST API endpoints.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from security.rbac import Role


class QueryRequest(BaseModel):
    query: str = Field(..., description="Natural language enterprise query", example="What were top sales in Q3?")
    role: Optional[str] = Field("ANALYST", description="User security role", example="ANALYST")
    tenant_id: Optional[str] = Field("tenant_enterprise_default", description="Tenant ID context")
    bypass_cache: Optional[bool] = Field(False, description="Bypass cache lookup")


class QueryResponse(BaseModel):
    query: str
    intent_route: str
    response: str
    overall_confidence: float
    execution_time_ms: float
    cache_hit: bool
    hitl_flagged: bool
    hitl_ticket_id: Optional[str] = None
    hitl_reason: Optional[str] = None
    generated_sql: Optional[str] = None
    sql_rows: List[Dict[str, Any]] = Field(default_factory=list)
    sql_columns: List[str] = Field(default_factory=list)
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    guardrail_matrix: List[Dict[str, Any]] = Field(default_factory=list)
    trace_id: Optional[str] = None


class IngestTextRequest(BaseModel):
    text: str = Field(..., description="Raw text content to ingest")
    title: str = Field("Enterprise Document", description="Document title")
    doc_id: Optional[str] = Field(None, description="Optional custom document ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


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
    operator_notes: Optional[str] = Field(None, description="Review notes")
    modified_sql: Optional[str] = Field(None, description="Optional edited SQL")


class HITLActionResponse(BaseModel):
    success: bool
    message: str
    ticket_id: str
    status: str
