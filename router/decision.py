"""
RAGTUNE Intent Router & Query Planning Engine - Decision Strategy Engine
Evaluates planning strategies, permission boundaries, cost caps, and capability selection.
"""


from auth.domain.models import SecurityContext
from router.domain import (
    CapabilityMetadata,
    CapabilityType,
    IntentCategory,
    PlanningStrategy,
)
from router.registry import CapabilityRegistry


class IntentDecisionEngine:
    def __init__(self, registry: CapabilityRegistry):
        self.registry = registry

    def select_capabilities_for_intent(
        self,
        intent: IntentCategory,
        strategy: PlanningStrategy,
        security_context: SecurityContext | None = None,
    ) -> list[CapabilityMetadata]:
        """
        Filters and selects optimal capabilities for target intent and strategy.
        """
        all_caps = self.registry.list_capabilities(enabled_only=True)

        # 1. Filter by Security & Permissions
        user_perms = (
            security_context.permissions
            if security_context and security_context.permissions
            else set()
        )
        permitted_caps = []
        for cap in all_caps:
            if not cap.required_permissions or all(p in user_perms for p in cap.required_permissions):
                permitted_caps.append(cap)

        # 2. Select based on Intent
        selected: list[CapabilityMetadata] = []

        if intent == IntentCategory.STRUCTURED_SQL:
            sql_caps = [
                c
                for c in permitted_caps
                if c.type
                in [CapabilityType.TEXT_TO_SQL, CapabilityType.ANALYTICS_ENGINE]
            ]
            selected.extend(sql_caps)

        elif intent == IntentCategory.UNSTRUCTURED_RAG:
            if strategy == PlanningStrategy.LOW_LATENCY:
                # Fast keyword search
                bm25 = [
                    c for c in permitted_caps if c.type == CapabilityType.RETRIEVAL_BM25
                ]
                selected.extend(bm25 if bm25 else permitted_caps[:1])
            elif strategy == PlanningStrategy.MAX_ACCURACY:
                # Both Dense Vector & Sparse BM25
                ret_caps = [
                    c
                    for c in permitted_caps
                    if c.type
                    in [CapabilityType.RETRIEVAL_VECTOR, CapabilityType.RETRIEVAL_BM25]
                ]
                selected.extend(ret_caps)
            else:
                # BALANCED: Dense Vector Search
                vec = [
                    c
                    for c in permitted_caps
                    if c.type == CapabilityType.RETRIEVAL_VECTOR
                ]
                selected.extend(vec)

        elif intent in [IntentCategory.HYBRID_ANALYTICS, IntentCategory.RESEARCH]:
            # Both SQL and Vector Retrieval
            hybrid = [
                c
                for c in permitted_caps
                if c.type
                in [CapabilityType.TEXT_TO_SQL, CapabilityType.RETRIEVAL_VECTOR]
            ]
            selected.extend(hybrid)

        elif intent == IntentCategory.SUMMARIZATION:
            sum_caps = [
                c
                for c in permitted_caps
                if c.type
                in [CapabilityType.RETRIEVAL_VECTOR, CapabilityType.DOCUMENT_SUMMARIZER]
            ]
            selected.extend(sum_caps)

        else:
            # Default fallback
            selected.extend(permitted_caps[:1])

        return selected
