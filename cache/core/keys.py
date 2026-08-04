"""
RAGTUNE Intelligent Caching System - Multi-Tenant Secure Key Builder
Constructs deterministic, namespaced cache keys enforcing multi-tenant boundary isolation.
"""

import hashlib
import json
from typing import Any


class TenantCacheKeyBuilder:
    @staticmethod
    def build_key(
        tenant_id: str, workspace_id: str, namespace: str, payload: Any
    ) -> str:
        """
        Builds a deterministic multi-tenant cache key:
        Format: ragtune:{tenant_id}:{workspace_id}:{namespace}:{hash}
        """
        t_clean = (tenant_id or "global_tenant").lower().strip()
        ws_clean = (workspace_id or "global_ws").lower().strip()
        ns_clean = (namespace or "general").lower().strip()

        # Hash payload
        if isinstance(payload, dict):
            serialized = json.dumps(payload, sort_keys=True, default=str)
        elif isinstance(payload, (list, tuple)):
            serialized = json.dumps(payload, default=str)
        else:
            serialized = str(payload)

        payload_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]
        return f"ragtune:{t_clean}:{ws_clean}:{ns_clean}:{payload_hash}"

    @staticmethod
    def build_tag(tenant_id: str, entity_type: str, entity_id: str) -> str:
        """Builds an invalidation tag (e.g. tag:acme_org:doc:doc_101)."""
        t_clean = (tenant_id or "global_tenant").lower().strip()
        type_clean = entity_type.lower().strip()
        id_clean = entity_id.strip()
        return f"tag:{t_clean}:{type_clean}:{id_clean}"
