"""
RAGTUNE - Enterprise API Gateway & REST Server
Exposes enterprise endpoints for intelligence queries, IAM, ingestion, HITL hub, and XAI tracing.
"""

import csv
import io
import json
from contextlib import asynccontextmanager
import os
import time

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from agents.graph import AgentOrchestrator
from agents.state import AgentState
from api.schemas import (
    DocumentDeleteResponse,
    DocumentItem,
    DocumentListResponse,
    ExportRequest,
    ExportResponse,
    HITLActionRequest,
    HITLActionResponse,
    IngestResponse,
    IngestTextRequest,
    QueryRequest,
    QueryResponse,
)
from auth.api.routes import router as auth_router
from cache.redis_client import EnterpriseCacheManager
from config.settings import settings
from demo_data.seed_data import seed_enterprise_db, seed_sample_documents
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
    xai_tracer=xai_tracer,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Seed initial enterprise sample data on startup if storage is empty."""
    db_path = (
        settings.DATABASE_URL.replace("sqlite:///", "")
        if settings.DATABASE_URL.startswith("sqlite:///")
        else None
    )
    if db_path and not os.path.exists(db_path):
        try:
            seed_enterprise_db(db_path)
        except Exception:  # nosec B110
            pass

    sample_dir = os.path.join("demo_data", "sample_documents")
    if not os.path.exists(sample_dir) or not os.listdir(sample_dir):
        try:
            seed_sample_documents(sample_dir)
        except Exception:  # nosec B110
            pass

    if os.path.exists(sample_dir):
        for f in os.listdir(sample_dir):
            f_path = os.path.join(sample_dir, f)
            if os.path.isfile(f_path):
                try:
                    chunks = doc_processor.process_file(f_path)
                    vector_store.add_chunks(chunks)
                except Exception:  # nosec B110
                    pass
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Enterprise Knowledge Intelligence Platform combining Identity & Access Management, RAG, Text-to-SQL, 9-Layer Guardrails, and Explainable AI.",
    lifespan=lifespan,
)

# Configure dynamic CORS for production frontend integration
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=True if cors_origins and cors_origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Identity & Access Management Router
app.include_router(auth_router)


@app.get("/health", tags=["Health"])
@app.get("/api/v1/health", tags=["Health"])
def health_check():
    """Platform health check."""
    return {
        "status": "HEALTHY",
        "platform": settings.APP_NAME,
        "version": settings.VERSION,
        "database_connected": db_connector.ping(),
        "cache_mode": cache_manager.get_stats()["mode"],
        "indexed_documents_chunks": len(vector_store.chunks),
    }


@app.get("/api/v1/analytics", tags=["Telemetry"])
def get_analytics():
    """Returns real-time platform analytics."""
    return {
        "status": "ACTIVE",
        "cache_stats": cache_manager.get_stats(),
        "vector_chunks": len(vector_store.chunks),
        "hitl_pending": len(hitl_manager.list_pending_tickets()),
    }


@app.get("/metrics", tags=["Telemetry"])
def get_metrics():
    """Returns system metrics for Prometheus scraping."""
    return {
        "ragtune_health_status": 1,
        "ragtune_vector_chunks_total": len(vector_store.chunks),
        "ragtune_hitl_pending_tickets": len(hitl_manager.list_pending_tickets()),
    }


@app.post("/api/v1/query", response_model=QueryResponse, tags=["Query Intelligence"])
def process_query(payload: QueryRequest):
    """
    Submits query to RAGTUNE agentic intelligence engine.
    """
    time.time()
    user_context = get_default_user_context(
        payload.role or "ANALYST", payload.tenant_id or "tenant_enterprise_default"
    )

    # Check Cache unless bypassed
    cache_key = f"query:{payload.role}:{hash(payload.query)}"
    if not payload.bypass_cache:
        cached = cache_manager.get(cache_key)
        if cached:
            cached["cache_hit"] = True
            return QueryResponse(**cached)

    # Initialize Agent State
    state = AgentState(user_query=payload.query, user_context=user_context)

    # Execute Multi-Agent Workflow Graph
    final_state = orchestrator.execute_workflow(state)

    # Prepare Response Data
    guardrail_matrix = []
    if final_state.post_guardrail_result:
        guardrail_matrix = [
            ev.model_dump()
            for ev in final_state.post_guardrail_result.layer_evaluations
        ]
    elif final_state.pre_guardrail_result:
        guardrail_matrix = [
            ev.model_dump() for ev in final_state.pre_guardrail_result.layer_evaluations
        ]

    # Ensure sql_columns is populated if sql_rows exist
    sql_cols = final_state.sql_columns
    if (
        not sql_cols
        and final_state.sql_rows
        and isinstance(final_state.sql_rows[0], dict)
    ):
        sql_cols = list(final_state.sql_rows[0].keys())

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
        sql_columns=sql_cols,
        retrieved_chunks=final_state.retrieved_chunks,
        guardrail_matrix=guardrail_matrix,
        trace_id=final_state.xai_trace.trace_id if final_state.xai_trace else None,
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
        metadata=payload.metadata,
    )
    vector_store.add_chunks(chunks)
    return IngestResponse(
        success=True,
        doc_id=payload.doc_id or "doc_auto",
        title=payload.title,
        chunks_created=len(chunks),
        message=f"Successfully indexed {len(chunks)} semantic chunk(s) into hybrid retriever.",
    )


@app.post("/api/v1/ingest/file", response_model=IngestResponse, tags=["Ingestion"])
async def ingest_file(file: UploadFile = File(...), title: str | None = Form(None)):
    """Ingests uploaded file (.md, .txt, .json, .csv) into hybrid vector index."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")

    if not doc_processor.is_supported_extension(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format for '{file.filename}'. Allowed formats: .txt, .md, .json, .csv, .pdf",
        )

    doc_title = title or file.filename
    doc_id = f"doc_{file.filename.replace(' ', '_').lower()}_{int(time.time())}"

    content = (await file.read()).decode("utf-8", errors="ignore")
    chunks = doc_processor.process_text(
        text=content,
        doc_id=doc_id,
        title=doc_title,
        metadata={"file_name": file.filename, "doc_id": doc_id, "title": doc_title},
    )
    vector_store.add_chunks(chunks)
    return IngestResponse(
        success=True,
        doc_id=doc_id,
        title=doc_title,
        chunks_created=len(chunks),
        message=f"Successfully uploaded and indexed '{file.filename}' into {len(chunks)} chunk(s).",
    )


@app.get("/api/v1/documents", response_model=DocumentListResponse, tags=["Ingestion"])
def list_documents():
    """Lists indexed document repository metadata and chunk counts."""
    docs_data = vector_store.list_documents()
    items = [DocumentItem(**d) for d in docs_data]
    return DocumentListResponse(
        total_documents=len(items),
        total_chunks=len(vector_store.chunks),
        documents=items,
    )


@app.delete(
    "/api/v1/documents/{doc_id}",
    response_model=DocumentDeleteResponse,
    tags=["Ingestion"],
)
def delete_document(doc_id: str):
    """Evicts document chunks by doc_id from hybrid vector store."""
    removed = vector_store.delete_document(doc_id)
    if removed == 0:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found")
    return DocumentDeleteResponse(
        success=True,
        doc_id=doc_id,
        chunks_removed=removed,
        message=f"Successfully deleted document '{doc_id}' and purged {removed} chunk(s).",
    )


@app.post(
    "/api/v1/export/query", response_model=ExportResponse, tags=["Query Intelligence"]
)
def export_query_result(payload: ExportRequest):
    """Exports Query Intelligence response as CSV or JSON report."""
    q_resp = payload.query_response
    fmt = payload.export_format.lower()

    if fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)

        if q_resp.sql_rows and q_resp.sql_columns:
            writer.writerow(q_resp.sql_columns)
            for row in q_resp.sql_rows:
                writer.writerow([row.get(c, "") for c in q_resp.sql_columns])
        else:
            writer.writerow(
                [
                    "Query",
                    "Intent Route",
                    "Overall Confidence",
                    "Execution Time (ms)",
                    "Cache Hit",
                ]
            )
            writer.writerow(
                [
                    q_resp.query,
                    q_resp.intent_route,
                    q_resp.overall_confidence,
                    q_resp.execution_time_ms,
                    q_resp.cache_hit,
                ]
            )
            writer.writerow([])
            writer.writerow(["Response Narrative"])
            writer.writerow([q_resp.response])

        csv_str = output.getvalue()
        return ExportResponse(
            filename=f"ragtune_export_{int(time.time())}.csv",
            export_format="csv",
            content_type="text/csv",
            content=csv_str,
        )
    else:
        json_str = json.dumps(q_resp.model_dump(), indent=2)
        return ExportResponse(
            filename=f"ragtune_export_{int(time.time())}.json",
            export_format="json",
            content_type="application/json",
            content=json_str,
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


@app.get("/api/v1/hitl/tickets/{ticket_id}", tags=["HITL Hub"])
def get_hitl_ticket(ticket_id: str):
    """Retrieves a specific HITL review ticket by ticket ID."""
    ticket = hitl_manager.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=404, detail=f"HITL Ticket '{ticket_id}' not found"
        )
    return ticket.model_dump()



@app.post("/api/v1/hitl/action", response_model=HITLActionResponse, tags=["HITL Hub"])
def resolve_hitl_ticket(payload: HITLActionRequest):
    """Resolves pending HITL review ticket."""
    success, msg, item = hitl_manager.resolve_ticket(
        ticket_id=payload.ticket_id,
        action=payload.action,
        operator_id=payload.operator_id,
        operator_notes=payload.operator_notes,
        modified_data={"sql": payload.modified_sql} if payload.modified_sql else None,
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return HITLActionResponse(
        success=True,
        message=msg,
        ticket_id=payload.ticket_id,
        status=item.status if item else "RESOLVED",
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

    @app.get("/style.css", include_in_schema=False)
    def serve_css():
        return FileResponse(os.path.join("frontend", "style.css"))

    @app.get("/app.js", include_in_schema=False)
    def serve_js():
        return FileResponse(os.path.join("frontend", "app.js"))

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def serve_frontend():
        index_path = os.path.join("frontend", "index.html")
        if os.path.exists(index_path):
            with open(index_path, encoding="utf-8") as f:
                return f.read()
        return "<h1>RAGTUNE Enterprise API Server Running</h1>"
