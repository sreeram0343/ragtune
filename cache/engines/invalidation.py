"""
RAGTUNE Intelligent Caching System - Tag-Based Event Invalidation Engine
Processes system lifecycle events to purge targeted cache entries across cache tiers.
"""

from typing import List, Callable, Dict, Any
from cache.core.provider import BaseCacheProvider
from cache.engines.semantic_cache import SemanticCacheEngine
from cache.core.keys import TenantCacheKeyBuilder


class CacheInvalidationEngine:
    def __init__(self, provider: BaseCacheProvider, semantic_cache: SemanticCacheEngine):
        self.provider = provider
        self.semantic_cache = semantic_cache
        self._event_subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def invalidate_document(self, tenant_id: str, document_id: str) -> int:
        """Invalidates all retrieval & hybrid search entries referencing document_id."""
        tag = TenantCacheKeyBuilder.build_tag(tenant_id, "doc", document_id)
        count_l1 = self.provider.delete_by_tag(tag)
        count_l2 = self.semantic_cache.invalidate_by_tag(tag)
        return count_l1 + count_l2

    def invalidate_sql_schema(self, tenant_id: str, schema_name: str) -> int:
        """Invalidates all Text-to-SQL generation entries for schema_name."""
        tag = TenantCacheKeyBuilder.build_tag(tenant_id, "schema", schema_name)
        count_l1 = self.provider.delete_by_tag(tag)
        count_l2 = self.semantic_cache.invalidate_by_tag(tag)
        return count_l1 + count_l2

    def invalidate_user_permissions(self, tenant_id: str, user_id: str) -> int:
        """Invalidates user security context & permission cache."""
        tag = TenantCacheKeyBuilder.build_tag(tenant_id, "user", user_id)
        return self.provider.delete_by_tag(tag)

    def handle_system_event(self, event_type: str, payload: Dict[str, Any]) -> int:
        """
        Dispatches system events:
        - 'document:updated': payload = {tenant_id, document_id}
        - 'schema:changed': payload = {tenant_id, schema_name}
        - 'user:permissions_changed': payload = {tenant_id, user_id}
        """
        tenant_id = payload.get("tenant_id", "global_tenant")
        if event_type == "document:updated":
            doc_id = payload.get("document_id", "")
            return self.invalidate_document(tenant_id, doc_id)
        elif event_type == "schema:changed":
            schema_name = payload.get("schema_name", "")
            return self.invalidate_sql_schema(tenant_id, schema_name)
        elif event_type == "user:permissions_changed":
            user_id = payload.get("user_id", "")
            return self.invalidate_user_permissions(tenant_id, user_id)
        return 0
