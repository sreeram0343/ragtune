"""
RAGTUNE Intelligent Caching System - Master Intelligent Cache Manager
Orchestrates L1 Exact Cache, L2 Semantic Cache, Single-Flight Coalescing, Tag Invalidation, and Telemetry.
"""

from collections.abc import Callable
from typing import Any

from cache.core.keys import TenantCacheKeyBuilder
from cache.core.provider import BaseCacheProvider, InMemoryLRUCacheProvider
from cache.engines.invalidation import CacheInvalidationEngine
from cache.engines.semantic_cache import SemanticCacheEngine
from cache.engines.single_flight import SingleFlightLock
from cache.telemetry.metrics import CacheTelemetryTracker


class IntelligentCacheManager:
    def __init__(self, provider: BaseCacheProvider | None = None):
        self.provider = (
            provider if provider else InMemoryLRUCacheProvider(capacity=10000)
        )
        self.semantic_cache = SemanticCacheEngine(
            similarity_threshold=0.92, max_entries=2000
        )
        self.single_flight = SingleFlightLock()
        self.invalidation = CacheInvalidationEngine(self.provider, self.semantic_cache)
        self.telemetry = CacheTelemetryTracker()

    def get_or_compute(
        self,
        tenant_id: str,
        workspace_id: str,
        namespace: str,
        payload: Any,
        compute_fn: Callable[[], Any],
        user_query: str | None = None,
        ttl_seconds: int | None = 3600,
        tags: list[str] | None = None,
    ) -> tuple[Any, str]:
        """
        Master cache lookup & computation method:
        1. Checks L1 Exact Match Hash Cache (0.1ms).
        2. Checks L2 Semantic Vector Cache (1.2ms) if user_query present.
        3. On miss, uses SingleFlightLock to execute compute_fn exactly once across concurrent callers.
        4. Writes back result to L1 and L2 caches with tags.
        Returns: (result: Any, cache_status: str ['L1_EXACT_HIT', 'L2_SEMANTIC_HIT', 'CACHE_MISS'])
        """
        key = TenantCacheKeyBuilder.build_key(
            tenant_id, workspace_id, namespace, payload
        )

        # 1. L1 Exact Match Cache
        l1_val = self.provider.get(key)
        if l1_val is not None:
            self.telemetry.record_exact_hit()
            return l1_val, "L1_EXACT_HIT"

        # 2. L2 Semantic Cache (if query text available)
        query_text = user_query or (
            payload.get("query") if isinstance(payload, dict) else None
        )
        if query_text:
            sem_match = self.semantic_cache.lookup(tenant_id, workspace_id, query_text)
            if sem_match:
                sem_val, score = sem_match
                self.telemetry.record_semantic_hit(similarity_score=score)
                return sem_val, f"L2_SEMANTIC_HIT (Score: {score:.2f})"

        # 3. Cache Miss -> Single-Flight Coalescing
        self.telemetry.record_miss()

        def _guarded_compute():
            res = compute_fn()
            # Store in L1 Exact Cache
            self.provider.set(key, res, ttl_seconds=ttl_seconds, tags=tags)
            # Store in L2 Semantic Cache if query text exists
            if query_text:
                self.semantic_cache.store(
                    tenant_id, workspace_id, query_text, res, tags=tags
                )
            return res

        result = self.single_flight.execute(key, _guarded_compute)
        return result, "CACHE_MISS"

    def invalidate_by_tag(self, tag: str) -> int:
        count_l1 = self.provider.delete_by_tag(tag)
        count_l2 = self.semantic_cache.invalidate_by_tag(tag)
        return count_l1 + count_l2

    def handle_event(self, event_type: str, payload: dict[str, Any]) -> int:
        return self.invalidation.handle_system_event(event_type, payload)

    def get_telemetry(self) -> dict[str, Any]:
        metrics = self.telemetry.get_metrics()
        provider_stats = self.provider.get_stats()
        metrics["provider_stats"] = provider_stats
        return metrics
