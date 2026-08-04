"""
RAGTUNE - LangGraph Agentic State Definitions
Defines typed state shared across multi-agent nodes in the execution pipeline.
"""

from typing import Any

from pydantic import BaseModel, Field

from guardrails.pipeline import PipelineResult
from security.rbac import UserContext
from xai.tracer import XAITrace


class AgentState(BaseModel):
    # User Input & Context
    user_query: str
    user_context: UserContext = Field(default_factory=UserContext)

    # Intent Routing
    intent_route: str = (
        "UNKNOWN"  # STRUCTURED_SQL, UNSTRUCTURED_RAG, HYBRID_FUSION, AMBIGUOUS
    )

    # Pre & Post Guardrail Results
    pre_guardrail_result: PipelineResult | None = None
    post_guardrail_result: PipelineResult | None = None

    # Structured Text-to-SQL Artifacts
    generated_sql: str | None = None
    sanitized_sql: str | None = None
    sql_rows: list[dict[str, Any]] = Field(default_factory=list)
    sql_columns: list[str] = Field(default_factory=list)
    sql_error: str | None = None

    # Unstructured RAG Artifacts
    retrieved_chunks: list[dict[str, Any]] = Field(default_factory=list)

    # Cache & Execution Flags
    cache_hit: bool = False
    hitl_flagged: bool = False
    hitl_ticket_id: str | None = None
    hitl_reason: str | None = None

    # Final Output & Evidence Synthesis
    final_response: str = ""
    overall_confidence: float = 1.0

    # Explainable AI Trace
    xai_trace: XAITrace | None = None

    # Telemetry
    execution_time_ms: float = 0.0
