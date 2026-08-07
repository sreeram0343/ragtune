"""
RAGTUNE - Test Suite for Explainable AI (XAI) Tracer
"""

from xai.tracer import XAITracer


def test_xai_trace_creation_and_latency():
    tracer = XAITracer()
    trace = tracer.create_trace("Select revenue from sales", intent_route="STRUCTURED_SQL")

    assert trace.user_query == "Select revenue from sales"
    assert trace.intent_route == "STRUCTURED_SQL"
    assert trace.trace_id.startswith("trace_")

    tracer.record_step(trace, "intent_router_node", "classified intent", latency_ms=12.5)
    tracer.record_step(trace, "sql_agent_node", "generated SQL", latency_ms=25.0)

    assert len(trace.execution_steps) == 2
    assert trace.get_total_latency_ms() == 37.5


def test_xai_get_step_by_node():
    tracer = XAITracer()
    trace = tracer.create_trace("What is our security policy?", intent_route="UNSTRUCTURED_RAG")

    tracer.record_step(trace, "pre_guardrail_node", "evaluated safety", latency_ms=5.0)
    tracer.record_step(trace, "rag_agent_node", "retrieved chunks", latency_ms=40.0)

    step = tracer.get_step_by_node(trace.trace_id, "rag_agent_node")
    assert step is not None
    assert step.agent_node == "rag_agent_node"
    assert step.action_taken == "retrieved chunks"

    # Non-existent node
    assert tracer.get_step_by_node(trace.trace_id, "non_existent_node") is None
    assert tracer.get_step_by_node("invalid_trace_id", "rag_agent_node") is None
