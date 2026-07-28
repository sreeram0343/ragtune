"""
RAGTUNE Intent Router & Query Planning Engine - Execution Plan Models
Defines structured ExecutionPlan, ExecutionStage, and ExecutionTask data containers.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from router.domain import IntentCategory, PlanningStrategy


class ExecutionTask(BaseModel):
    task_id: str
    capability_id: str
    name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    est_cost_usd: float = 0.0
    est_latency_ms: float = 0.0


class ExecutionStage(BaseModel):
    stage_id: int
    stage_name: str
    tasks: List[ExecutionTask] = Field(default_factory=list)
    parallel_execution: bool = False
    dependencies: List[int] = Field(default_factory=list)


class ExecutionPlan(BaseModel):
    plan_id: str
    query_text: str
    intent: IntentCategory
    strategy: PlanningStrategy
    confidence_score: float = 1.0
    stages: List[ExecutionStage] = Field(default_factory=list)
    total_est_cost_usd: float = 0.0
    total_est_latency_ms: float = 0.0
    risk_level: str = "LOW"
    requires_hitl_approval: bool = False
    explanation: str = ""
