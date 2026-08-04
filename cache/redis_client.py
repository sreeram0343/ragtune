"""
RAGTUNE - Redis & In-Memory Multi-Tier Caching Layer
Provides exact match caching, semantic vector caching, and SQL result caching with TTL.
"""

import json
import time
from typing import Any

from config.settings import settings

try:
    import redis

    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class EnterpriseCacheManager:
    def __init__(self):
        self.use_redis = False
        self.redis_client = None
        self.memory_cache: dict[str, dict[str, Any]] = {}
        self.stats = {"hits": 0, "misses": 0, "entries": 0}

        if HAS_REDIS and settings.REDIS_URL and settings.ENABLE_CACHE:
            try:
                client = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1)
                client.ping()
                self.redis_client = client
                self.use_redis = True
            except Exception:
                self.use_redis = False

    def get(self, cache_key: str) -> dict[str, Any] | None:
        """Retrieves cached payload by key."""
        if not settings.ENABLE_CACHE:
            return None

        if self.use_redis and self.redis_client:
            try:
                val = self.redis_client.get(f"ragtune:{cache_key}")
                if val:
                    self.stats["hits"] += 1
                    return json.loads(val)
            except Exception:
                pass

        # In-memory cache fallback
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if entry["expires_at"] > time.time():
                self.stats["hits"] += 1
                return entry["data"]
            else:
                del self.memory_cache[cache_key]

        self.stats["misses"] += 1
        return None

    def set(
        self,
        cache_key: str,
        value: dict[str, Any],
        ttl_seconds: int = settings.CACHE_TTL_SECONDS,
    ):
        """Stores value in cache with specified TTL."""
        if not settings.ENABLE_CACHE:
            return

        if self.use_redis and self.redis_client:
            try:
                self.redis_client.setex(
                    f"ragtune:{cache_key}", ttl_seconds, json.dumps(value, default=str)
                )
                return
            except Exception:
                pass

        # In-memory cache set
        self.memory_cache[cache_key] = {
            "data": value,
            "expires_at": time.time() + ttl_seconds,
        }
        self.stats["entries"] = len(self.memory_cache)

    def get_stats(self) -> dict[str, Any]:
        """Returns cache telemetry statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests) if total_requests > 0 else 0.0
        return {
            "mode": "Redis" if self.use_redis else "In-Memory",
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate_pct": round(hit_rate * 100, 2),
            "cached_items_count": (
                len(self.memory_cache) if not self.use_redis else "managed_by_redis"
            ),
        }

    def clear(self):
        """Clears cache entries."""
        self.memory_cache.clear()
        if self.use_redis and self.redis_client:
            try:
                keys = self.redis_client.keys("ragtune:*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception:
                pass
        self.stats = {"hits": 0, "misses": 0, "entries": 0}
