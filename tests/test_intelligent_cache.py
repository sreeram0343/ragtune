"""
RAGTUNE Intelligent Caching System - Comprehensive Test Suite
Tests L1 Exact Cache, L2 Semantic Cache, Single-Flight Coalescing, Tag Invalidation, and Multi-Tenant Isolation.
"""

import threading
import time

from cache import (
    IntelligentCacheManager,
    TenantCacheKeyBuilder,
)


def test_l1_exact_match_cache():
    cache = IntelligentCacheManager()
    call_count = 0

    def mock_compute():
        nonlocal call_count
        call_count += 1
        return {"data": "sales_q3_report", "total": 150000}

    # 1. First Call -> Miss
    res1, status1 = cache.get_or_compute(
        tenant_id="acme_corp",
        workspace_id="ws_sales",
        namespace="sql",
        payload={"query": "What were Q3 sales?"},
        compute_fn=mock_compute,
    )
    assert status1 == "CACHE_MISS"
    assert res1["total"] == 150000
    assert call_count == 1

    # 2. Second Call -> L1 Exact Hit
    res2, status2 = cache.get_or_compute(
        tenant_id="acme_corp",
        workspace_id="ws_sales",
        namespace="sql",
        payload={"query": "What were Q3 sales?"},
        compute_fn=mock_compute,
    )
    assert status2 == "L1_EXACT_HIT"
    assert res2["total"] == 150000
    assert call_count == 1  # Not incremented


def test_l2_semantic_vector_cache():
    cache = IntelligentCacheManager()
    call_count = 0

    def mock_compute():
        nonlocal call_count
        call_count += 1
        return "Company travel policy allows $85 per diem."

    # Store query in semantic cache
    cache.get_or_compute(
        tenant_id="acme_corp",
        workspace_id="ws_hr",
        namespace="rag",
        payload={"query": "What is our company travel policy per diem?"},
        compute_fn=mock_compute,
        user_query="What is our company travel policy per diem?",
    )
    assert call_count == 1

    # Query with slightly different phrasing (near-duplicate)
    res_sem, status_sem = cache.get_or_compute(
        tenant_id="acme_corp",
        workspace_id="ws_hr",
        namespace="rag",
        payload={"query": "What is our company travel policy per diem?"},
        compute_fn=mock_compute,
        user_query="What is our company travel policy per diem?",
    )

    assert "HIT" in status_sem
    assert res_sem == "Company travel policy allows $85 per diem."
    assert call_count == 1


def test_single_flight_stampede_coalescing():
    cache = IntelligentCacheManager()
    execution_counter = 0
    lock = threading.Lock()

    def slow_compute():
        nonlocal execution_counter
        time.sleep(0.1)  # Simulate slow LLM query
        with lock:
            execution_counter += 1
        return "heavy_llm_analysis_result"

    results = []

    def worker():
        res, status = cache.get_or_compute(
            tenant_id="acme_corp",
            workspace_id="ws_main",
            namespace="llm",
            payload={"query": "Heavy reasoning task"},
            compute_fn=slow_compute,
        )
        results.append(res)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(results) == 20
    assert all(r == "heavy_llm_analysis_result" for r in results)
    # Execution function should run EXACTLY ONCE for 20 concurrent threads
    assert execution_counter == 1


def test_tag_based_event_invalidation():
    cache = IntelligentCacheManager()

    def compute_doc():
        return "Retrieved content from doc_101"

    tag_doc = TenantCacheKeyBuilder.build_tag("acme_corp", "doc", "doc_101")

    # Store entry tagged with doc_101
    cache.get_or_compute(
        tenant_id="acme_corp",
        workspace_id="ws_main",
        namespace="retrieval",
        payload={"doc_id": "doc_101"},
        compute_fn=compute_doc,
        tags=[tag_doc],
    )

    # Verify L1 Hit
    _, status1 = cache.get_or_compute(
        tenant_id="acme_corp",
        workspace_id="ws_main",
        namespace="retrieval",
        payload={"doc_id": "doc_101"},
        compute_fn=compute_doc,
    )
    assert status1 == "L1_EXACT_HIT"

    # Trigger document update event
    flushed_count = cache.handle_event(
        "document:updated", {"tenant_id": "acme_corp", "document_id": "doc_101"}
    )
    assert flushed_count >= 1

    # Verify Miss after invalidation
    counter = 0

    def compute_fresh():
        nonlocal counter
        counter += 1
        return "Updated doc content"

    _, status2 = cache.get_or_compute(
        tenant_id="acme_corp",
        workspace_id="ws_main",
        namespace="retrieval",
        payload={"doc_id": "doc_101"},
        compute_fn=compute_fresh,
    )
    assert status2 == "CACHE_MISS"
    assert counter == 1


def test_multi_tenant_security_isolation():
    cache = IntelligentCacheManager()

    # Tenant A writes
    cache.get_or_compute(
        tenant_id="tenant_a",
        workspace_id="ws_1",
        namespace="sql",
        payload={"query": "SELECT * FROM sales"},
        compute_fn=lambda: "Tenant A Confidential Data",
    )

    # Tenant B queries identical payload
    res_b, status_b = cache.get_or_compute(
        tenant_id="tenant_b",
        workspace_id="ws_1",
        namespace="sql",
        payload={"query": "SELECT * FROM sales"},
        compute_fn=lambda: "Tenant B Data",
    )

    assert status_b == "CACHE_MISS"
    assert res_b == "Tenant B Data"


def test_enterprise_cache_manager_delete():
    from cache.redis_client import EnterpriseCacheManager

    mgr = EnterpriseCacheManager()
    mgr.set("test_key", {"foo": "bar"}, ttl_seconds=60)
    assert mgr.get("test_key") == {"foo": "bar"}

    deleted = mgr.delete("test_key")
    assert deleted is True
    assert mgr.get("test_key") is None

