"""
RAGTUNE - Test Suite for REST API Gateway
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"


def test_query_endpoint():
    response = client.post(
        "/api/v1/query",
        json={"query": "What is our response time SLA policy for Severity 1 outages?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "response" in data
    assert "intent_route" in data


def test_schema_endpoint():
    response = client.get("/api/v1/schema")
    assert response.status_code == 200
    data = response.json()
    assert "schema" in data


def test_hitl_queue_endpoint():
    response = client.get("/api/v1/hitl/queue")
    assert response.status_code == 200
    data = response.json()
    assert "pending_count" in data
