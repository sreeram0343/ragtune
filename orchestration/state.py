"""
RAGTUNE Workflow Orchestration Engine - Core State Definitions & Schema
Defines typed state containers, workflow status lifecycles, and node execution history.
"""

from enum import StrEnum
from typing import Any, TypedDict

from pydantic import BaseModel


class WorkflowStatusEnum(StrEnum):
    PENDING = "PENDING"
    INITIALIZING = "INITIALIZING"
    ROUTING = "ROUTING"
    EXECUTING = "EXECUTING"
    EVALUATING = "EVALUATING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    RESUMING = "RESUMING"
    RETRYING = "RETRYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


class NodeExecutionRecord(BaseModel):
    node_name: str
    started_at: float
    completed_at: float | None = None
    status: str = "SUCCESS"
    output_summary: str | None = None
    error_detail: str | None = None
    latency_ms: float = 0.0


class OrchestrationState(TypedDict, total=False):
    workflow_id: str
    request_id: str
    tenant_id: str
    workspace_id: str
    user_id: str
    user_query: str
    intent: str | None  # "STRUCTURED", "UNSTRUCTURED", "HYBRID"
    status: str  # WorkflowStatusEnum
    current_node: str
    step_history: list[dict[str, Any]]

    # Node outputs
    sql_query: str | None
    sql_result: dict[str, Any] | None
    rag_documents: list[dict[str, Any]] | None
    fusion_output: dict[str, Any] | None

    # Quality & Policy Evaluation
    evaluation_score: float
    groundedness_score: float
    policy_passed: bool
    requires_hitl: bool
    hitl_ticket_id: str | None
    hitl_decision: str | None  # "APPROVED", "REJECTED"

    # Fault tolerance
    retry_count: int
    max_retries: int
    error_message: str | None

    # Final Result
    final_response: str | None
    metadata: dict[str, Any]
