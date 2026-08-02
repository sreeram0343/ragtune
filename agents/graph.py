"""
RAGTUNE - LangGraph Orchestrator Engine
Assembles state graph nodes into a cohesive multi-agent execution machine.
"""

import time
from typing import Dict, Any
from agents.state import AgentState
from agents.nodes import AgentNodeExecutors
from text2sql.engine import Text2SQLEngine
from retrieval.hybrid_search import HybridSearchEngine
from retrieval.reranker import CrossEncoderReranker
from guardrails.pipeline import GuardrailPipeline
from hitl.manager import HITLManager
from xai.tracer import XAITracer, XAITrace


class AgentOrchestrator:
    def __init__(
        self,
        text2sql_engine: Text2SQLEngine,
        hybrid_retriever: HybridSearchEngine,
        reranker: CrossEncoderReranker,
        guardrail_pipeline: GuardrailPipeline,
        hitl_manager: HITLManager,
        xai_tracer: XAITracer
    ):
        self.executors = AgentNodeExecutors(
            text2sql_engine=text2sql_engine,
            hybrid_retriever=hybrid_retriever,
            reranker=reranker,
            guardrail_pipeline=guardrail_pipeline,
            hitl_manager=hitl_manager,
            xai_tracer=xai_tracer
        )
        self.tracer = xai_tracer

    def execute_workflow(self, state: AgentState) -> AgentState:
        """
        Executes multi-agent workflow sequentially through the compiled graph.
        """
        start_time = time.time()

        # Initialize XAI Trace
        trace = self.tracer.create_trace(state.user_query)
        state.xai_trace = trace

        # Step 1: Pre-Execution Guardrails
        state = self.executors.pre_guardrail_node(state)
        if state.hitl_flagged and state.pre_guardrail_result and not state.pre_guardrail_result.pre_execution_passed:
            state.execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return state

        # Step 2: Intent Routing
        state = self.executors.intent_router_node(state)

        # Step 3: Domain Agents Execution
        route = state.intent_route
        if route == "STRUCTURED_SQL":
            state = self.executors.sql_agent_node(state)
        elif route in ["UNSTRUCTURED_RAG", "SUMMARIZATION", "POLICY_LOOKUP"]:
            state = self.executors.rag_agent_node(state)
        else:  # HYBRID_FUSION
            state = self.executors.sql_agent_node(state)
            state = self.executors.rag_agent_node(state)

        # Step 4: Evidence Synthesis
        state = self.executors.evidence_synthesis_node(state)

        # Step 5: Post-Execution Guardrails & HITL Evaluation
        state = self.executors.post_guardrail_node(state)

        state.execution_time_ms = round((time.time() - start_time) * 1000, 2)
        return state
