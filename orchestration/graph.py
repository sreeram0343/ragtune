"""
RAGTUNE Workflow Orchestration Engine - LangGraph StateGraph Compilation
Constructs and compiles the deterministic workflow state machine using LangGraph.
"""

from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from orchestration.state import OrchestrationState, WorkflowStatusEnum
from orchestration.nodes import (
    init_node, router_node, sql_node, rag_node, fusion_node,
    evaluation_node, hitl_gate_node, retry_node, synthesis_node, fallback_node
)


def _route_after_router(state: OrchestrationState) -> Literal["sql_node", "rag_node", "fusion_node"]:
    intent = state.get("intent", "HYBRID")
    if intent == "STRUCTURED":
        return "sql_node"
    elif intent == "UNSTRUCTURED":
        return "rag_node"
    return "fusion_node"


def _route_after_evaluation(state: OrchestrationState) -> Literal["synthesis_node", "hitl_gate_node", "retry_node"]:
    if state.get("hitl_decision") == "REJECTED" or state.get("requires_hitl", False):
        return "hitl_gate_node"
    if not state.get("policy_passed", True):
        return "retry_node"
    return "synthesis_node"


def _route_after_hitl(state: OrchestrationState) -> Literal["synthesis_node", "fallback_node", "__end__"]:
    decision = state.get("hitl_decision")
    if decision == "APPROVED":
        return "synthesis_node"
    elif decision == "REJECTED":
        return "fallback_node"
    # Freeze workflow in suspended state until operator decision is submitted
    return END


def _route_after_retry(state: OrchestrationState) -> Literal["evaluation_node", "fallback_node"]:
    status = state.get("status")
    if status == WorkflowStatusEnum.FAILED.value:
        return "fallback_node"
    return "evaluation_node"


class WorkflowGraphBuilder:
    @staticmethod
    def build_graph():
        """Constructs and compiles the complete LangGraph Workflow StateGraph."""
        builder = StateGraph(OrchestrationState)

        # 1. Add Workflow State Nodes
        builder.add_node("init_node", init_node)
        builder.add_node("router_node", router_node)
        builder.add_node("sql_node", sql_node)
        builder.add_node("rag_node", rag_node)
        builder.add_node("fusion_node", fusion_node)
        builder.add_node("evaluation_node", evaluation_node)
        builder.add_node("hitl_gate_node", hitl_gate_node)
        builder.add_node("retry_node", retry_node)
        builder.add_node("synthesis_node", synthesis_node)
        builder.add_node("fallback_node", fallback_node)

        # 2. Add Fixed Edges
        builder.set_entry_point("init_node")
        builder.add_edge("init_node", "router_node")

        # 3. Add Conditional Routing Edges
        builder.add_conditional_edges("router_node", _route_after_router)
        builder.add_edge("sql_node", "evaluation_node")
        builder.add_edge("rag_node", "evaluation_node")
        builder.add_edge("fusion_node", "evaluation_node")

        builder.add_conditional_edges("evaluation_node", _route_after_evaluation)
        builder.add_conditional_edges("hitl_gate_node", _route_after_hitl)
        builder.add_conditional_edges("retry_node", _route_after_retry)

        # 4. Terminal Edges
        builder.add_edge("synthesis_node", END)
        builder.add_edge("fallback_node", END)

        return builder.compile()
