"""
RAGTUNE - Test Suite for Multi-Agent Workflow Engine
"""

from agents.graph import AgentOrchestrator
from agents.state import AgentState
from guardrails.pipeline import GuardrailPipeline
from hitl.manager import HITLManager
from retrieval.hybrid_search import HybridSearchEngine
from retrieval.reranker import CrossEncoderReranker
from security.rbac import get_default_user_context
from storage.db_connector import DBConnector
from storage.document_processor import DocumentProcessor
from storage.vector_store import HybridVectorStore
from text2sql.engine import Text2SQLEngine
from xai.tracer import XAITracer


def test_agent_workflow_execution():
    db = DBConnector("sqlite:///:memory:")
    DocumentProcessor()
    store = HybridVectorStore()
    retriever = HybridSearchEngine(store)
    reranker = CrossEncoderReranker()
    text2sql = Text2SQLEngine(db)
    pipeline = GuardrailPipeline()
    hitl = HITLManager()
    tracer = XAITracer()

    orchestrator = AgentOrchestrator(
        text2sql_engine=text2sql,
        hybrid_retriever=retriever,
        reranker=reranker,
        guardrail_pipeline=pipeline,
        hitl_manager=hitl,
        xai_tracer=tracer,
    )

    user_ctx = get_default_user_context()
    state = AgentState(
        user_query="What were total customer sales in 2024?", user_context=user_ctx
    )
    final_state = orchestrator.execute_workflow(state)

    assert final_state.intent_route in ["STRUCTURED_SQL", "HYBRID_FUSION"]
    assert final_state.xai_trace is not None
    assert len(final_state.xai_trace.execution_steps) > 0
