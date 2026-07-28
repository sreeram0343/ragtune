"""
RAGTUNE - LangGraph Agentic Nodes Module
Executes specialized sub-agent logic within the graph workflow.
"""

import time
from typing import Dict, Any, List
from agents.state import AgentState
from text2sql.engine import Text2SQLEngine
from retrieval.hybrid_search import HybridSearchEngine
from retrieval.reranker import CrossEncoderReranker
from guardrails.pipeline import GuardrailPipeline
from hitl.manager import HITLManager
from xai.tracer import XAITracer, XAITrace


class AgentNodeExecutors:
    def __init__(
        self,
        text2sql_engine: Text2SQLEngine,
        hybrid_retriever: HybridSearchEngine,
        reranker: CrossEncoderReranker,
        guardrail_pipeline: GuardrailPipeline,
        hitl_manager: HITLManager,
        xai_tracer: XAITracer
    ):
        self.text2sql = text2sql_engine
        self.retriever = hybrid_retriever
        self.reranker = reranker
        self.guardrails = guardrail_pipeline
        self.hitl = hitl_manager
        self.tracer = xai_tracer

    def pre_guardrail_node(self, state: AgentState) -> AgentState:
        """Pre-execution guardrails validation node."""
        t0 = time.time()
        pre_res = self.guardrails.run_pre_execution(state.user_query, state.user_context)
        state.pre_guardrail_result = pre_res
        
        if state.xai_trace:
            self.tracer.record_step(
                state.xai_trace,
                agent_node="PreGuardrailNode",
                action_taken="Ran Layers 1-4 Pre-Execution Guardrails",
                latency_ms=(time.time() - t0) * 1000,
                details={"pre_passed": pre_res.pre_execution_passed, "sanitized_query": pre_res.sanitized_query}
            )

        if not pre_res.pre_execution_passed:
            state.hitl_flagged = True
            state.hitl_reason = pre_res.hitl_reason
            state.final_response = f"Query flagged by pre-execution guardrails: {pre_res.hitl_reason}"

        return state

    def intent_router_node(self, state: AgentState) -> AgentState:
        """Classifies query intent to route execution."""
        t0 = time.time()
        query = state.pre_guardrail_result.sanitized_query if state.pre_guardrail_result else state.user_query
        q_lower = query.lower()

        # Structured indicators
        sql_keywords = ["how many", "count", "total", "sales", "revenue", "orders", "customers", "table", "sum", "average"]
        # Unstructured indicators
        rag_keywords = ["policy", "contract", "terms", "document", "reimbursement", "clause", "sla", "definition", "guideline"]

        has_sql = any(k in q_lower for k in sql_keywords)
        has_rag = any(k in q_lower for k in rag_keywords)

        if has_sql and has_rag:
            route = "HYBRID_FUSION"
        elif has_sql:
            route = "STRUCTURED_SQL"
        elif has_rag:
            route = "UNSTRUCTURED_RAG"
        else:
            route = "HYBRID_FUSION"

        state.intent_route = route
        if state.xai_trace:
            state.xai_trace.intent_route = route
            self.tracer.record_step(
                state.xai_trace,
                agent_node="IntentRouterNode",
                action_taken=f"Routed query intent to '{route}'",
                latency_ms=(time.time() - t0) * 1000
            )

        return state

    def sql_agent_node(self, state: AgentState) -> AgentState:
        """Executes Text-to-SQL synthesis and query execution."""
        t0 = time.time()
        query = state.pre_guardrail_result.sanitized_query if state.pre_guardrail_result else state.user_query

        sql_res = self.text2sql.process_query(query)
        state.generated_sql = sql_res.generated_sql
        state.sanitized_sql = sql_res.sanitized_sql
        state.sql_rows = sql_res.rows
        state.sql_columns = sql_res.columns
        state.sql_error = sql_res.error_message

        if state.xai_trace:
            state.xai_trace.generated_sql = sql_res.sanitized_sql
            self.tracer.record_step(
                state.xai_trace,
                agent_node="SQLAgentNode",
                action_taken="Generated and executed SQL query",
                latency_ms=(time.time() - t0) * 1000,
                details={"sql": sql_res.sanitized_sql, "rows_returned": sql_res.row_count, "success": sql_res.success}
            )

        return state

    def rag_agent_node(self, state: AgentState) -> AgentState:
        """Executes Hybrid Search (BM25 + Vector) and Cross-Encoder Re-ranking."""
        t0 = time.time()
        query = state.pre_guardrail_result.sanitized_query if state.pre_guardrail_result else state.user_query

        candidates = self.retriever.search(query, top_k=10)
        reranked_chunks = self.reranker.rerank(query, candidates, top_k=5)
        state.retrieved_chunks = reranked_chunks

        if state.xai_trace:
            self.tracer.attach_attributions(state.xai_trace, reranked_chunks)
            self.tracer.record_step(
                state.xai_trace,
                agent_node="RAGAgentNode",
                action_taken="Retrieved and re-ranked evidence document chunks",
                latency_ms=(time.time() - t0) * 1000,
                details={"candidates_found": len(candidates), "top_reranked": len(reranked_chunks)}
            )

        return state

    def evidence_synthesis_node(self, state: AgentState) -> AgentState:
        """Synthesizes structured SQL tabular data and unstructured text evidence."""
        t0 = time.time()
        narrative_parts = []

        if state.intent_route in ["STRUCTURED_SQL", "HYBRID_FUSION"] and state.sql_rows:
            narrative_parts.append(f"**Structured Database Findings:** Found {len(state.sql_rows)} matching record(s).")
            if len(state.sql_rows) == 1:
                first_row = state.sql_rows[0]
                details_str = ", ".join(f"{k}: {v}" for k, v in list(first_row.items())[:5])
                narrative_parts.append(f"- Summary: {details_str}")
            else:
                narrative_parts.append(f"- Query executed: `{state.sanitized_sql}`")

        if state.intent_route in ["UNSTRUCTURED_RAG", "HYBRID_FUSION"] and state.retrieved_chunks:
            narrative_parts.append("\n**Unstructured Knowledge Evidence:**")
            for chunk in state.retrieved_chunks[:3]:
                snippet = chunk.get('content', '')[:150].replace('\n', ' ')
                narrative_parts.append(f"- [{chunk.get('title')}] (Relevance: {chunk.get('rerank_score', 0):.2f}): \"{snippet}...\"")

        if not narrative_parts:
            narrative_parts.append("No direct records or matching document snippets were found for the query criteria.")

        state.final_response = "\n".join(narrative_parts)

        if state.xai_trace:
            self.tracer.record_step(
                state.xai_trace,
                agent_node="EvidenceSynthesisNode",
                action_taken="Fused findings into grounded response narrative",
                latency_ms=(time.time() - t0) * 1000
            )

        return state

    def post_guardrail_node(self, state: AgentState) -> AgentState:
        """Post-execution 9-layer guardrails validation node."""
        t0 = time.time()
        context_snippets = [c.get("content", "") for c in state.retrieved_chunks] if state.retrieved_chunks else None

        post_res = self.guardrails.run_post_execution(
            pre_result=state.pre_guardrail_result,
            user_context=state.user_context,
            generated_sql=state.generated_sql,
            retrieved_chunks=context_snippets,
            raw_response=state.final_response
        )

        state.post_guardrail_result = post_res
        state.overall_confidence = post_res.overall_confidence

        if state.xai_trace:
            self.tracer.attach_guardrail_matrix(state.xai_trace, post_res.layer_evaluations)
            state.xai_trace.overall_confidence = post_res.overall_confidence
            state.xai_trace.hitl_flagged = post_res.hitl_triggered
            state.xai_trace.hitl_reason = post_res.hitl_reason

            self.tracer.record_step(
                state.xai_trace,
                agent_node="PostGuardrailNode",
                action_taken="Evaluated Post-Execution Guardrails (Layers 5-9)",
                latency_ms=(time.time() - t0) * 1000,
                details={"post_passed": post_res.post_execution_passed, "confidence": post_res.overall_confidence}
            )

        # Check HITL Trigger condition
        if post_res.hitl_triggered:
            state.hitl_flagged = True
            state.hitl_reason = post_res.hitl_reason
            ticket = self.hitl.create_ticket(
                user_id=state.user_context.user_id,
                tenant_id=state.user_context.tenant_id,
                original_query=state.user_query,
                reason=post_res.hitl_reason or "Guardrail violation or low confidence trigger",
                confidence_score=post_res.overall_confidence,
                context_data={
                    "sql": state.sanitized_sql,
                    "response": state.final_response,
                    "trace_id": state.xai_trace.trace_id if state.xai_trace else None
                }
            )
            state.hitl_ticket_id = ticket.ticket_id

        return state
