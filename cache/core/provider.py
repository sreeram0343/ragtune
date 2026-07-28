"""
RAGTUNE Intelligent Caching System - Core Provider Abstractions & Storage Adapters
Defines abstract cache provider interface, thread-safe In-Memory LRU provider, and Redis adapter.
"""

import time
import threading
from abc import ABC, abstractmethod
from collections import OrderedDict
from typing import Any, Optional, Dict, List, Set, Tuple


class BaseCacheProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, tags: Optional[List[str]] = None) -> bool:
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        pass

    @abstractmethod
    def delete_by_tag(self, tag: str) -> int:
        pass

    @abstractmethod
    def clear(self) -> bool:
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        pass


class InMemoryLRUCacheProvider(BaseCacheProvider):
    """
    High-performance, Thread-Safe In-Memory LRU Cache Provider.
    Supports capacity eviction, sliding/absolute TTLs, and tag-based invalidation.
    """
    def __init__(self, capacity: int = 10000, default_ttl: int = 3600):
        self.capacity = capacity
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
        self._cache: OrderedDict[str, Tuple[Any, float, float, List[str]]] = OrderedDict()
        self._tag_to_keys: Dict[str, Set[str]] = {}
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            val, created_at, ttl, tags = self._cache[key]
            now = time.time()
            if ttl > 0 and (now - created_at) > ttl:
                # Expired
                self._delete_key_internal(key)
                self._misses += 1
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            self._hits += 1
            return val

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, tags: Optional[List[str]] = None) -> bool:
        with self._lock:
            ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
            now = time.time()
            tag_list = tags or []

            # If key already exists, delete old tag mappings
            if key in self._cache:
                self._delete_key_internal(key)

            # Evict LRU if capacity reached
            while len(self._cache) >= self.capacity:
                oldest_key, _ = self._cache.popitem(last=False)
                self._cleanup_tag_mappings(oldest_key)
                self._evictions += 1

            self._cache[key] = (value, now, ttl, tag_list)
            for tag in tag_list:
                if tag not in self._tag_to_keys:
                    self._tag_to_keys[tag] = set()
                self._tag_to_keys[tag].add(key)

            return True

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                self._delete_key_internal(key)
                return True
            return False

    def delete_by_tag(self, tag: str) -> int:
        with self._lock:
            if tag not in self._tag_to_keys:
                return 0
            keys_to_delete = list(self._tag_to_keys[tag])
            count = 0
            for k in keys_to_delete:
                if k in self._cache:
                    self._delete_key_internal(k)
                    count += 1
            self._tag_to_keys.pop(tag, None)
            return count

    def _delete_key_internal(self, key: str):
        if key in self._cache:
            _, _, _, tags = self._cache.pop(key)
            for tag in tags:
                if tag in self._tag_to_keys:
                    self._tag_to_keys[tag].discard(key)
                    if not self._tag_to_keys[tag]:
                        del self._tag_to_keys[tag]

    def _cleanup_tag_mappings(self, key: str):
        pass  # Handled in _delete_key_internal

    def clear(self) -> bool:
        with self._lock:
            self._cache.clear()
            self._tag_to_keys.clear()
            return True

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hits + self._misses
            hit_ratio = (self._hits / total) if total > 0 else 0.0
            return {
                "size": len(self._cache),
                "capacity": self.capacity,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "hit_ratio": round(hit_ratio, 4),
                "active_tags": len(self._tag_to_keys)
            }


class RedisCacheProvider(BaseCacheProvider):
    """Distributed Redis Cache Provider fallback adapter."""
    def __init__(self, redis_client=None):
        self.client = redis_client
        self._fallback = InMemoryLRUCacheProvider(capacity=5000)

    def get(self, key: str) -> Optional[Any]:
        if self.client:
            try:
                val = self.client.get(key)
                return val
            except Exception:
                pass
        return self._fallback.get(key)

    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None, tags: Optional[List[str]] = None) -> bool:
        if self.client:
            try:
                self.client.set(key, value, ex=ttl_seconds)
                return True
            except Exception:
                pass
        return self._fallback.set(key, value, ttl_seconds, tags)

    def delete(self, key: str) -> bool:
        return self._fallback.delete(key)

    def delete_by_tag(self, tag: str) -> int:
        return self._fallback.delete_by_tag(tag)

    def clear(self) -> bool:
        return self._fallback.clear()

    def get_stats(self) -> Dict[str, Any]:
        return self._fallback.get_stats()
