"""
RAGTUNE - Explainable AI (XAI) & Attribution Engine
Logs step-by-step agent execution graphs, guardrail evaluation matrices, and context attributions.
"""

import time
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ExecutionStep(BaseModel):
    step_num: int
    agent_node: str
    action_taken: str
    latency_ms: float
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class XAITrace(BaseModel):
    trace_id: str = Field(default_factory=lambda: f"trace_{uuid.uuid4().hex[:12]}")
    user_query: str
    intent_route: str
    overall_confidence: float = 1.0
    execution_steps: List[ExecutionStep] = Field(default_factory=list)
    guardrail_matrix: List[Dict[str, Any]] = Field(default_factory=list)
    attributions: List[Dict[str, Any]] = Field(default_factory=list)
    generated_sql: Optional[str] = None
    cache_hit: bool = False
    hitl_flagged: bool = False
    hitl_reason: Optional[str] = None
    created_at: float = Field(default_factory=time.time)


class XAITracer:
    def __init__(self):
        self.trace_store: Dict[str, XAITrace] = {}

    def create_trace(self, user_query: str, intent_route: str = "UNKNOWN") -> XAITrace:
        """Initializes a new XAI Trace object."""
        trace = XAITrace(user_query=user_query, intent_route=intent_route)
        self.trace_store[trace.trace_id] = trace
        return trace

    def record_step(
        self,
        trace: XAITrace,
        agent_node: str,
        action_taken: str,
        latency_ms: float,
        details: Optional[Dict[str, Any]] = None
    ):
        """Appends an execution step to the trace."""
        step_num = len(trace.execution_steps) + 1
        step = ExecutionStep(
            step_num=step_num,
            agent_node=agent_node,
            action_taken=action_taken,
            latency_ms=round(latency_ms, 2),
            details=details or {}
        )
        trace.execution_steps.append(step)

    def attach_guardrail_matrix(self, trace: XAITrace, pipeline_evaluations: List[Any]):
        """Attaches 9-layer guardrail evaluation breakdown."""
        matrix = []
        for ev in pipeline_evaluations:
            matrix.append({
                "layer_num": getattr(ev, "layer_num", 0),
                "layer_name": getattr(ev, "layer_name", ""),
                "passed": getattr(ev, "passed", True),
                "score": getattr(ev, "score", 1.0),
                "details": getattr(ev, "details", "")
            })
        trace.guardrail_matrix = matrix

    def attach_attributions(self, trace: XAITrace, chunks: List[Dict[str, Any]]):
        """Attaches retrieved document evidence chunks as attributions."""
        attr_list = []
        for c in chunks:
            attr_list.append({
                "chunk_id": c.get("chunk_id"),
                "doc_title": c.get("title"),
                "content_snippet": c.get("content", "")[:200] + "...",
                "rerank_score": round(c.get("rerank_score", c.get("rrf_score", 0.0)), 4),
                "rank": c.get("final_rank", c.get("rank", 1))
            })
        trace.attributions = attr_list

    def get_trace(self, trace_id: str) -> Optional[XAITrace]:
        """Retrieves trace object by trace_id."""
        return self.trace_store.get(trace_id)
