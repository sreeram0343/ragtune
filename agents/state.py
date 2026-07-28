"""
RAGTUNE - LangGraph Agentic State Definitions
Defines typed state shared across multi-agent nodes in the execution pipeline.
"""

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field
from security.rbac import UserContext
from guardrails.pipeline import PipelineResult
from xai.tracer import XAITrace


class AgentState(BaseModel):
    # User Input & Context
    user_query: str
    user_context: UserContext = Field(default_factory=UserContext)
    
    # Intent Routing
    intent_route: str = "UNKNOWN"  # STRUCTURED_SQL, UNSTRUCTURED_RAG, HYBRID_FUSION, AMBIGUOUS
    
    # Pre & Post Guardrail Results
    pre_guardrail_result: Optional[PipelineResult] = None
    post_guardrail_result: Optional[PipelineResult] = None
    
    # Structured Text-to-SQL Artifacts
    generated_sql: Optional[str] = None
    sanitized_sql: Optional[str] = None
    sql_rows: List[Dict[str, Any]] = Field(default_factory=list)
    sql_columns: List[str] = Field(default_factory=list)
    sql_error: Optional[str] = None
    
    # Unstructured RAG Artifacts
    retrieved_chunks: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Cache & Execution Flags
    cache_hit: bool = False
    hitl_flagged: bool = False
    hitl_ticket_id: Optional[str] = None
    hitl_reason: Optional[str] = None
    
    # Final Output & Evidence Synthesis
    final_response: str = ""
    overall_confidence: float = 1.0
    
    # Explainable AI Trace
    xai_trace: Optional[XAITrace] = None
    
    # Telemetry
    execution_time_ms: float = 0.0
