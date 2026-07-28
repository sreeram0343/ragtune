"""
RAGTUNE Intent Router & Query Planning Engine - Master Query Planner
Transforms enriched security requests into optimized, structured ExecutionPlan objects.
"""

import uuid
from typing import Optional, Dict, Any
from input_security.framework.stage import EnrichedSecurityRequest
from router.domain import IntentCategory, PlanningStrategy
from router.registry import CapabilityRegistry
from router.classifier import IntentClassifier
from router.decision import IntentDecisionEngine
from router.plan import ExecutionPlan, ExecutionStage, ExecutionTask


class QueryPlanner:
    def __init__(self, registry: Optional[CapabilityRegistry] = None):
        self.registry = registry if registry else CapabilityRegistry()
        self.classifier = IntentClassifier()
        self.decision_engine = IntentDecisionEngine(self.registry)

    def create_execution_plan(
        self,
        security_request: EnrichedSecurityRequest,
        preferred_strategy: PlanningStrategy = PlanningStrategy.BALANCED
    ) -> ExecutionPlan:
        """
        Main query planning API:
        Analyzes query, discovers capabilities, applies strategy, and builds ExecutionPlan.
        """
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        query_text = security_request.sanitized_query
        sec_ctx = security_request.security_context

        # 1. Classify Intent & Confidence
        intent, confidence = self.classifier.classify(query_text)

        # 2. Select Capabilities via Decision Engine
        selected_caps = self.decision_engine.select_capabilities_for_intent(
            intent=intent,
            strategy=preferred_strategy,
            security_context=sec_ctx
        )

        # 3. Construct Execution Stages & Tasks
        stages: List[ExecutionStage] = []
        total_cost = 0.0
        total_latency = 0.0

        if intent == IntentCategory.HYBRID_ANALYTICS:
            # Parallel Stage: SQL + Vector Retrieval
            parallel_tasks = []
            max_parallel_latency = 0.0
            for i, cap in enumerate(selected_caps):
                task = ExecutionTask(
                    task_id=f"task_parallel_{i+1}",
                    capability_id=cap.capability_id,
                    name=cap.name,
                    est_cost_usd=cap.cost_per_call,
                    est_latency_ms=cap.est_latency_ms
                )
                parallel_tasks.append(task)
                total_cost += cap.cost_per_call
                if cap.est_latency_ms > max_parallel_latency:
                    max_parallel_latency = cap.est_latency_ms

            stages.append(ExecutionStage(
                stage_id=1,
                stage_name="Parallel Hybrid Data Retrieval & SQL Execution",
                tasks=parallel_tasks,
                parallel_execution=True
            ))
            total_latency += max_parallel_latency

        else:
            # Sequential Stages
            for i, cap in enumerate(selected_caps):
                task = ExecutionTask(
                    task_id=f"task_{i+1}",
                    capability_id=cap.capability_id,
                    name=cap.name,
                    est_cost_usd=cap.cost_per_call,
                    est_latency_ms=cap.est_latency_ms
                )
                stage = ExecutionStage(
                    stage_id=i+1,
                    stage_name=f"Stage {i+1}: {cap.name}",
                    tasks=[task],
                    parallel_execution=False,
                    dependencies=[i] if i > 0 else []
                )
                stages.append(stage)
                total_cost += cap.cost_per_call
                total_latency += cap.est_latency_ms

        requires_hitl = security_request.cumulative_risk_score > 40.0 or "sensitive" in query_text.lower()
        risk_level = "HIGH" if requires_hitl else "LOW"

        explanation = (
            f"Query classified as '{intent.value}' (Confidence: {confidence:.2f}). "
            f"Applied '{preferred_strategy.value}' strategy selecting {len(selected_caps)} capability task(s)."
        )

        return ExecutionPlan(
            plan_id=plan_id,
            query_text=query_text,
            intent=intent,
            strategy=preferred_strategy,
            confidence_score=confidence,
            stages=stages,
            total_est_cost_usd=round(total_cost, 5),
            total_est_latency_ms=round(total_latency, 2),
            risk_level=risk_level,
            requires_hitl_approval=requires_hitl,
            explanation=explanation
        )
