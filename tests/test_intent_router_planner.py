"""
RAGTUNE Intent Router & Query Planning Engine - Comprehensive Test Suite
Tests intent classification, dynamic capability registration, plan generation, strategy evaluation, and cost estimation.
"""

import json

from auth.domain.models import SecurityContext, UserStatus
from input_security.framework.stage import (
    EnrichedSecurityRequest,
    SecurityRequestContainer,
    TrustLevel,
)
from router import (
    CapabilityMetadata,
    CapabilityRegistry,
    CapabilityType,
    IntentCategory,
    PlanningStrategy,
    QueryPlanner,
)


def _build_dummy_security_request(
    query: str, permissions=None
) -> EnrichedSecurityRequest:
    sec_ctx = SecurityContext(
        user_id="usr_planner_test",
        email="planner@enterprise.com",
        status=UserStatus.ACTIVE,
        org_id="org_acme",
        workspace_id="ws_main",
        permissions=permissions or {"workspace:read"},
    )

    container = SecurityRequestContainer(
        raw_body=json.dumps({"query": query}).encode("utf-8"),
        user_query=query,
        user_context=sec_ctx,
    )

    return EnrichedSecurityRequest(
        request_id="req_plan_001",
        original_container=container,
        sanitized_query=query,
        sanitized_payload={"query": query},
        security_context=sec_ctx,
        trust_level=TrustLevel.HIGH,
        cumulative_risk_score=0.0,
        cleared_for_orchestration=True,
    )


def test_intent_classification_categories():
    planner = QueryPlanner()

    # 1. SQL Query
    req_sql = _build_dummy_security_request("What were total sales revenue in Q3?")
    plan_sql = planner.create_execution_plan(req_sql)
    assert plan_sql.intent == IntentCategory.STRUCTURED_SQL

    # 2. RAG Document Query
    req_rag = _build_dummy_security_request(
        "What is our enterprise travel policy per diem?"
    )
    plan_rag = planner.create_execution_plan(req_rag)
    assert plan_rag.intent == IntentCategory.UNSTRUCTURED_RAG

    # 3. Hybrid Analytics Query
    req_hybrid = _build_dummy_security_request(
        "What is total sales revenue under contract terms?"
    )
    plan_hybrid = planner.create_execution_plan(req_hybrid)
    assert plan_hybrid.intent == IntentCategory.HYBRID_ANALYTICS


def test_dynamic_capability_registration():
    registry = CapabilityRegistry()

    # Register custom external tool
    custom_cap = CapabilityMetadata(
        capability_id="cap_custom_weather_api",
        name="External Weather Telemetry API",
        type=CapabilityType.WEB_SEARCH,
        cost_per_call=0.005,
        est_latency_ms=180.0,
        description="Fetches real-time weather analytics",
    )
    registry.register_capability(custom_cap)

    retrieved = registry.get_capability("cap_custom_weather_api")
    assert retrieved is not None
    assert retrieved.name == "External Weather Telemetry API"


def test_planning_strategies_low_latency_vs_max_accuracy():
    planner = QueryPlanner()
    req = _build_dummy_security_request("What is our enterprise travel policy?")

    # Low Latency strategy
    plan_fast = planner.create_execution_plan(
        req, preferred_strategy=PlanningStrategy.LOW_LATENCY
    )
    # Max Accuracy strategy
    plan_accurate = planner.create_execution_plan(
        req, preferred_strategy=PlanningStrategy.MAX_ACCURACY
    )

    assert plan_fast.total_est_latency_ms <= plan_accurate.total_est_latency_ms
    assert len(plan_accurate.stages[0].tasks) >= len(plan_fast.stages[0].tasks)


def test_execution_plan_structure_and_cost_metrics():
    planner = QueryPlanner()
    req = _build_dummy_security_request(
        "Compute total sales revenue under agreement terms"
    )

    plan = planner.create_execution_plan(req)

    assert plan.plan_id.startswith("plan_")
    assert plan.total_est_cost_usd > 0.0
    assert plan.total_est_latency_ms > 0.0
    assert len(plan.stages) >= 1
    assert "Confidence" in plan.explanation
