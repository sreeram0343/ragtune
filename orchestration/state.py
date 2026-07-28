"""
RAGTUNE Workflow Orchestration Engine - Core State Definitions & Schema
Defines typed state containers, workflow status lifecycles, and node execution history.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, TypedDict
from pydantic import BaseModel, Field


class WorkflowStatusEnum(str, Enum):
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
    completed_at: Optional[float] = None
    status: str = "SUCCESS"
    output_summary: Optional[str] = None
    error_detail: Optional[str] = None
    latency_ms: float = 0.0


class OrchestrationState(TypedDict, total=False):
    workflow_id: str
    request_id: str
    tenant_id: str
    workspace_id: str
    user_id: str
    user_query: str
    intent: Optional[str]  # "STRUCTURED", "UNSTRUCTURED", "HYBRID"
    status: str  # WorkflowStatusEnum
    current_node: str
    step_history: List[Dict[str, Any]]
    
    # Node outputs
    sql_query: Optional[str]
    sql_result: Optional[Dict[str, Any]]
    rag_documents: Optional[List[Dict[str, Any]]]
    fusion_output: Optional[Dict[str, Any]]
    
    # Quality & Policy Evaluation
    evaluation_score: float
    groundedness_score: float
    policy_passed: bool
    requires_hitl: bool
    hitl_ticket_id: Optional[str]
    hitl_decision: Optional[str]  # "APPROVED", "REJECTED"
    
    # Fault tolerance
    retry_count: int
    max_retries: int
    error_message: Optional[str]
    
    # Final Result
    final_response: Optional[str]
    metadata: Dict[str, Any]
