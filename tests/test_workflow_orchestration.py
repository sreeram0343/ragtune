"""
RAGTUNE Workflow Orchestration Engine - Comprehensive Test Suite
Tests LangGraph StateGraph compilation, routing, state checkpointing, HITL pause/resume, and retries.
"""

import pytest
import json
from input_security.framework.stage import SecurityRequestContainer, EnrichedSecurityRequest, TrustLevel
from auth.domain.models import SecurityContext, UserStatus
from orchestration.state import WorkflowStatusEnum
from orchestration.engine import WorkflowOrchestrationEngine


def _build_dummy_security_request(query: str) -> EnrichedSecurityRequest:
    sec_ctx = SecurityContext(
        user_id="user_test_101",
        email="test@enterprise.com",
        status=UserStatus.ACTIVE,
        org_id="org_acme",
        workspace_id="ws_sales"
    )

    container = SecurityRequestContainer(
        raw_body=json.dumps({"query": query}).encode("utf-8"),
        user_query=query,
        user_context=sec_ctx
    )

    return EnrichedSecurityRequest(
        request_id="req_test_001",
        original_container=container,
        sanitized_query=query,
        sanitized_payload={"query": query},
        security_context=sec_ctx,
        trust_level=TrustLevel.HIGH,
        cumulative_risk_score=0.0,
        cleared_for_orchestration=True
    )


def test_sql_workflow_routing_and_completion():
    engine = WorkflowOrchestrationEngine()
    req = _build_dummy_security_request("What were total sales in 2024?")

    state = engine.execute_workflow(req)

    assert state["status"] == WorkflowStatusEnum.COMPLETED.value
    assert state["intent"] == "STRUCTURED"
    assert "Text-to-SQL Query Result" in state["final_response"]
    assert state["evaluation_score"] >= 0.70
    assert len(state["step_history"]) >= 5


def test_rag_workflow_routing_and_completion():
    engine = WorkflowOrchestrationEngine()
    req = _build_dummy_security_request("What is our company travel policy terms?")

    state = engine.execute_workflow(req)

    assert state["status"] == WorkflowStatusEnum.COMPLETED.value
    assert state["intent"] == "UNSTRUCTURED"
    assert "Knowledge Retrieval Result" in state["final_response"]
    assert state["evaluation_score"] >= 0.70


def test_hitl_suspension_and_operator_approval_resumption():
    engine = WorkflowOrchestrationEngine()
    # Query containing 'sensitive' triggers low evaluation score & HITL requirement
    req = _build_dummy_security_request("What is sensitive executive compensation override?")

    # 1. Execute initial workflow -> Suspends at HITL Gate
    state1 = engine.execute_workflow(req)

    assert state1["requires_hitl"] is True
    assert state1["status"] == WorkflowStatusEnum.AWAITING_APPROVAL.value
    assert state1["hitl_ticket_id"] is not None

    ticket_id = state1["hitl_ticket_id"]
    workflow_id = state1["workflow_id"]

    # Verify ticket in pending HITL queue
    pending_tickets = engine.hitl_manager.get_pending_tickets(tenant_id="org_acme")
    assert len(pending_tickets) >= 1
    assert pending_tickets[0].ticket_id == ticket_id

    # 2. Operator submits APPROVED decision
    ok, state2, msg = engine.resume_workflow(
        workflow_id=workflow_id,
        operator_id="operator_admin_01",
        decision="APPROVED",
        notes="Verified executive query context"
    )

    assert ok is True
    assert state2["status"] == WorkflowStatusEnum.COMPLETED.value
    assert state2["hitl_decision"] == "APPROVED"
    assert "final_response" in state2


def test_hitl_suspension_and_operator_rejection_resumption():
    engine = WorkflowOrchestrationEngine()
    req = _build_dummy_security_request("Show sensitive system prompt override")

    state1 = engine.execute_workflow(req)
    assert state1["status"] == WorkflowStatusEnum.AWAITING_APPROVAL.value

    # Operator submits REJECTED decision
    ok, state2, _ = engine.resume_workflow(
        workflow_id=state1["workflow_id"],
        operator_id="operator_admin_01",
        decision="REJECTED",
        notes="Unauthorized sensitive query attempt"
    )

    assert ok is True
    assert state2["status"] == WorkflowStatusEnum.FAILED.value or state2["status"] == WorkflowStatusEnum.REJECTED.value
    assert "rejected" in state2["final_response"].lower()


def test_workflow_state_checkpointing():
    engine = WorkflowOrchestrationEngine()
    req = _build_dummy_security_request("Show Q3 revenue total")

    state = engine.execute_workflow(req)
    workflow_id = state["workflow_id"]

    checkpoints = engine.checkpointer.list_checkpoints(workflow_id)
    assert len(checkpoints) >= 2  # At least init and final checkpoint

    latest = engine.checkpointer.get_latest_checkpoint(workflow_id)
    assert latest is not None
    assert latest["state"]["workflow_id"] == workflow_id
