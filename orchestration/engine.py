"""
RAGTUNE Workflow Orchestration Engine - Master Engine Harness
Exposes unified workflow execution and HITL resumption APIs powered by LangGraph.
"""

import uuid
from typing import Any

from input_security.framework.stage import EnrichedSecurityRequest
from orchestration.checkpointer import WorkflowCheckpointer
from orchestration.graph import WorkflowGraphBuilder
from orchestration.hitl import HumanApprovalManager
from orchestration.state import OrchestrationState, WorkflowStatusEnum


class WorkflowOrchestrationEngine:
    def __init__(self):
        self.compiled_graph = WorkflowGraphBuilder.build_graph()
        self.checkpointer = WorkflowCheckpointer()
        self.hitl_manager = HumanApprovalManager()

    def execute_workflow(
        self,
        security_request: EnrichedSecurityRequest,
        custom_metadata: dict[str, Any] | None = None,
    ) -> OrchestrationState:
        """
        Submits an EnrichedSecurityRequest to the LangGraph workflow engine.
        Executes state machine nodes, checkpoints state snapshots, and suspends if HITL triggered.
        """
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        sec_ctx = security_request.security_context

        initial_state: OrchestrationState = {
            "workflow_id": workflow_id,
            "request_id": security_request.request_id,
            "tenant_id": (
                sec_ctx.org_id if sec_ctx and sec_ctx.org_id else "global_tenant"
            ),
            "workspace_id": (
                sec_ctx.workspace_id
                if sec_ctx and sec_ctx.workspace_id
                else "global_ws"
            ),
            "user_id": sec_ctx.user_id if sec_ctx else "anonymous",
            "user_query": security_request.sanitized_query,
            "status": WorkflowStatusEnum.PENDING.value,
            "current_node": "init_node",
            "step_history": [],
            "retry_count": 0,
            "max_retries": 3,
            "evaluation_score": 0.0,
            "groundedness_score": 0.0,
            "policy_passed": True,
            "requires_hitl": False,
            "metadata": custom_metadata or {},
        }

        # 1. Save Initial Checkpoint
        self.checkpointer.save_checkpoint(workflow_id, initial_state, "init")

        # 2. Invoke LangGraph State Machine
        final_state: OrchestrationState = self.compiled_graph.invoke(initial_state)

        # 3. Save Post-Execution Checkpoint
        self.checkpointer.save_checkpoint(
            workflow_id, final_state, final_state.get("current_node", "end")
        )

        # 4. If suspended for HITL, register approval ticket in HITL manager
        if final_state.get("requires_hitl") and final_state.get("hitl_ticket_id"):
            self.hitl_manager.create_ticket(
                ticket_id=final_state["hitl_ticket_id"],
                workflow_id=workflow_id,
                tenant_id=final_state["tenant_id"],
                workspace_id=final_state["workspace_id"],
                user_query=final_state["user_query"],
                reason=f"Evaluation score ({final_state.get('evaluation_score')}) below threshold or security policy flag",
            )

        return final_state

    def resume_workflow(
        self,
        workflow_id: str,
        operator_id: str,
        decision: str,  # "APPROVED" or "REJECTED"
        notes: str | None = None,
    ) -> tuple[bool, OrchestrationState | None, str]:
        """
        Resumes a suspended workflow following human operator review.
        """
        latest_ckpt = self.checkpointer.get_latest_checkpoint(workflow_id)
        if not latest_ckpt:
            return (
                False,
                None,
                f"Workflow '{workflow_id}' not found in state checkpoints",
            )

        state: OrchestrationState = latest_ckpt["state"]

        if state.get("status") not in [
            WorkflowStatusEnum.AWAITING_APPROVAL.value,
            "SUSPENDED",
        ]:
            return (
                False,
                state,
                f"Workflow is not awaiting approval (Status: {state.get('status')})",
            )

        # Submit HITL decision in manager
        ticket_id = state.get("hitl_ticket_id")
        if ticket_id:
            self.hitl_manager.submit_decision(ticket_id, operator_id, decision, notes)

        state["hitl_decision"] = decision
        state["requires_hitl"] = False

        # Resume graph execution
        resumed_state: OrchestrationState = self.compiled_graph.invoke(state)

        # Save post-resumption checkpoint
        self.checkpointer.save_checkpoint(
            workflow_id, resumed_state, "resume_post_hitl"
        )

        return (
            True,
            resumed_state,
            f"Workflow resumed successfully with decision '{decision}'",
        )
