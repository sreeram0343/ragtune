"""
RAGTUNE - Document Management, Report Export & Expanded Intent Tests
Validates file upload, document cataloging, document eviction, query exports, and new intent routes.
"""

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_file_ingestion_and_document_lifecycle():
    # 1. Test File Ingestion
    file_content = b"# Enterprise Security & Compliance Guidelines\n\nAll data at rest must be encrypted with AES-256."
    response = client.post(
        "/api/v1/ingest/file",
        files={"file": ("security_policy.md", file_content, "text/markdown")},
        data={"title": "Security Policy MD"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["chunks_created"] >= 1
    doc_id = data["doc_id"]

    # 2. Test List Documents
    list_res = client.get("/api/v1/documents")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total_documents"] >= 1
    assert any(d["doc_id"] == doc_id for d in list_data["documents"])

    # 3. Test Delete Document
    del_res = client.delete(f"/api/v1/documents/{doc_id}")
    assert del_res.status_code == 200
    del_data = del_res.json()
    assert del_data["success"] is True
    assert del_data["chunks_removed"] >= 1

    # 4. Verify Document Evicted
    list_res2 = client.get("/api/v1/documents")
    list_data2 = list_res2.json()
    assert not any(d["doc_id"] == doc_id for d in list_data2["documents"])


def test_query_result_export_json_and_csv():
    # Execute query first
    q_res = client.post(
        "/api/v1/query",
        json={"query": "What is our SLA uptime policy?", "bypass_cache": True},
    )
    assert q_res.status_code == 200
    query_response = q_res.json()

    # Test Export JSON
    exp_json = client.post(
        "/api/v1/export/query",
        json={"export_format": "json", "query_response": query_response},
    )
    assert exp_json.status_code == 200
    json_data = exp_json.json()
    assert json_data["export_format"] == "json"
    assert "ragtune_export" in json_data["filename"]
    assert "overall_confidence" in json_data["content"]

    # Test Export CSV
    exp_csv = client.post(
        "/api/v1/export/query",
        json={"export_format": "csv", "query_response": query_response},
    )
    assert exp_csv.status_code == 200
    csv_data = exp_csv.json()
    assert csv_data["export_format"] == "csv"
    assert "Query" in csv_data["content"]


def test_summarization_and_policy_intent_routing():
    # Test Summarization Route
    sum_res = client.post(
        "/api/v1/query",
        json={
            "query": "Summarize our SLA terms and outage procedures",
            "bypass_cache": True,
        },
    )
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["intent_route"] in [
        "SUMMARIZATION",
        "HYBRID_FUSION",
        "UNSTRUCTURED_RAG",
    ]

    # Test Policy Lookup Route
    pol_res = client.post(
        "/api/v1/query",
        json={
            "query": "What is the compliance policy for security governance?",
            "bypass_cache": True,
        },
    )
    assert pol_res.status_code == 200
    pol_data = pol_res.json()
    assert pol_data["intent_route"] in [
        "POLICY_LOOKUP",
        "HYBRID_FUSION",
        "UNSTRUCTURED_RAG",
    ]


def test_unsupported_file_extension_ingestion():
    response = client.post(
        "/api/v1/ingest/file",
        files={"file": ("unsupported_script.exe", b"binary content", "application/octet-stream")},
        data={"title": "Executable File"},
    )
    assert response.status_code == 400
    data = response.json()
    assert "Unsupported file format" in data["detail"]


def test_hybrid_vector_store_get_chunk_by_id():
    from storage.document_processor import DocumentChunk
    from storage.vector_store import HybridVectorStore

    store = HybridVectorStore()
    chunk = DocumentChunk(
        chunk_id="chunk_test_123",
        doc_id="doc_1",
        title="Test Document",
        content="Sample content for testing chunk lookup.",
        chunk_index=0,
        token_count=10,
    )

    store.add_chunks([chunk])

    retrieved = store.get_chunk_by_id("chunk_test_123")
    assert retrieved is not None
    assert retrieved.chunk_id == "chunk_test_123"
    assert store.get_chunk_by_id("non_existent_chunk") is None


