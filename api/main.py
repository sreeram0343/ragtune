"""
RAGTUNE - Enterprise API Gateway & REST Server
Exposes enterprise endpoints for intelligence queries, ingestion, HITL hub, and XAI tracing.
"""

import time
import os
from typing import Dict, Any, List
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from config.settings import settings
from security.rbac import get_default_user_context, UserContext
from storage.db_connector import DBConnector
from storage.document_processor import DocumentProcessor
from storage.vector_store import HybridVectorStore
from retrieval.hybrid_search import HybridSearchEngine
from retrieval.reranker import CrossEncoderReranker
from text2sql.engine import Text2SQLEngine
from guardrails.pipeline import GuardrailPipeline
from cache.redis_client import EnterpriseCacheManager
from hitl.manager import HITLManager
from xai.tracer import XAITracer
from agents.state import AgentState
from agents.graph import AgentOrchestrator
from api.schemas import (
    QueryRequest, QueryResponse,
    IngestTextRequest, IngestResponse,
    HITLActionRequest, HITLActionResponse
)

# Initialize Core Services
db_connector = DBConnector()
doc_processor = DocumentProcessor()
vector_store = HybridVectorStore()
retriever = HybridSearchEngine(vector_store)
reranker = CrossEncoderReranker()
text2sql_engine = Text2SQLEngine(db_connector)
guardrail_pipeline = GuardrailPipeline()
cache_manager = EnterpriseCacheManager()
hitl_manager = HITLManager()
xai_tracer = XAITracer()

orchestrator = AgentOrchestrator(
    text2sql_engine=text2sql_engine,
    hybrid_retriever=retriever,
    reranker=reranker,
    guardrail_pipeline=guardrail_pipeline,
    hitl_manager=hitl_manager,
    xai_tracer=xai_tracer
)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Enterprise Knowledge Intelligence Platform combining RAG, Text-to-SQL, 9-Layer Guardrails, and Explainable AI."
)

# Enable CORS for modern web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Seed initial enterprise sample data on startup if storage is empty."""
    # Process sample document if available
    sample_dir = os.path.join("demo_data", "sample_documents")
    if os.path.exists(sample_dir):
        for f in os.listdir(sample_dir):
            f_path = os.path.join(sample_dir, f)
            if os.path.isfile(f_path):
                try:
                    chunks = doc_processor.process_file(f_path)
                    vector_store.add_chunks(chunks)
                except Exception:
                    pass


@app.get("/health", tags=["Health"])
def health_check():
    """Platform health check."""
    return {
        "status": "HEALTHY",
        "platform": settings.APP_NAME,
        "version": settings.VERSION,
        "cache_mode": cache_manager.get_stats()["mode"],
        "indexed_documents_chunks": len(vector_store.chunks)
    }


@app.post("/api/v1/query", response_model=QueryResponse, tags=["Query Intelligence"])
def process_query(payload: QueryRequest):
    """
    Submits query to RAGTUNE agentic intelligence engine.
    """
    t0 = time.time()
    user_context = get_default_user_context(payload.role or "ANALYST", payload.tenant_id or "tenant_enterprise_default")

    # Check Cache unless bypassed
    cache_key = f"query:{payload.role}:{hash(payload.query)}"
    if not payload.bypass_cache:
        cached = cache_manager.get(cache_key)
        if cached:
            cached["cache_hit"] = True
            return QueryResponse(**cached)

    # Initialize Agent State
    state = AgentState(
        user_query=payload.query,
        user_context=user_context
    )

    # Execute Multi-Agent Workflow Graph
    final_state = orchestrator.execute_workflow(state)

    # Prepare Response Data
    guardrail_matrix = []
    if final_state.post_guardrail_result:
        guardrail_matrix = [ev.model_dump() for ev in final_state.post_guardrail_result.layer_evaluations]
    elif final_state.pre_guardrail_result:
        guardrail_matrix = [ev.model_dump() for ev in final_state.pre_guardrail_result.layer_evaluations]

    response_data = QueryResponse(
        query=payload.query,
        intent_route=final_state.intent_route,
        response=final_state.final_response,
        overall_confidence=final_state.overall_confidence,
        execution_time_ms=final_state.execution_time_ms,
        cache_hit=False,
        hitl_flagged=final_state.hitl_flagged,
        hitl_ticket_id=final_state.hitl_ticket_id,
        hitl_reason=final_state.hitl_reason,
        generated_sql=final_state.sanitized_sql,
        sql_rows=final_state.sql_rows,
        sql_columns=final_state.sql_columns,
        retrieved_chunks=final_state.retrieved_chunks,
        guardrail_matrix=guardrail_matrix,
        trace_id=final_state.xai_trace.trace_id if final_state.xai_trace else None
    )

    # Save to Cache if clean pass
    if not final_state.hitl_flagged and final_state.overall_confidence >= 0.8:
        cache_manager.set(cache_key, response_data.model_dump())

    return response_data


@app.post("/api/v1/ingest/text", response_model=IngestResponse, tags=["Ingestion"])
def ingest_text(payload: IngestTextRequest):
    """Ingests raw text string into hybrid document index."""
    chunks = doc_processor.process_text(
        text=payload.text,
        doc_id=payload.doc_id or f"doc_{int(time.time())}",
        title=payload.title,
        metadata=payload.metadata
    )
    vector_store.add_chunks(chunks)
    return IngestResponse(
        success=True,
        doc_id=payload.doc_id or "doc_auto",
        title=payload.title,
        chunks_created=len(chunks),
        message=f"Successfully indexed {len(chunks)} semantic chunk(s) into hybrid retriever."
    )


@app.get("/api/v1/schema", tags=["Database"])
def get_database_schema():
    """Returns database schema metadata catalog."""
    return {"schema": [t.model_dump() for t in db_connector.get_schema_metadata()]}


@app.get("/api/v1/hitl/queue", tags=["HITL Hub"])
def get_hitl_queue():
    """Returns active pending HITL review tickets."""
    tickets = hitl_manager.list_pending_tickets()
    return {"pending_count": len(tickets), "tickets": [t.model_dump() for t in tickets]}


@app.post("/api/v1/hitl/action", response_model=HITLActionResponse, tags=["HITL Hub"])
def resolve_hitl_ticket(payload: HITLActionRequest):
    """Resolves pending HITL review ticket."""
    success, msg, item = hitl_manager.resolve_ticket(
        ticket_id=payload.ticket_id,
        action=payload.action,
        operator_id=payload.operator_id,
        operator_notes=payload.operator_notes,
        modified_data={"sql": payload.modified_sql} if payload.modified_sql else None
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return HITLActionResponse(
        success=True,
        message=msg,
        ticket_id=payload.ticket_id,
        status=item.status if item else "RESOLVED"
    )


@app.get("/api/v1/xai/{trace_id}", tags=["Explainable AI"])
def get_xai_trace(trace_id: str):
    """Fetches Explainable AI step-by-step execution trace."""
    trace = xai_tracer.get_trace(trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail=f"XAI Trace '{trace_id}' not found")
    return trace.model_dump()


@app.get("/api/v1/cache/stats", tags=["Telemetry"])
def get_cache_stats():
    """Returns cache metrics."""
    return cache_manager.get_stats()


# Serve static web frontend
if os.path.exists("frontend"):
    app.mount("/static", StaticFiles(directory="frontend"), name="static")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def serve_frontend():
        index_path = os.path.join("frontend", "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                return f.read()
        return "<h1>RAGTUNE Enterprise API Server Running</h1>"
