"""
RAGTUNE Intent Router & Query Planning Engine - Dynamic Capability Registry
Maintains discoverable platform tools, execution costs, latencies, and required permission scopes.
"""

import threading
from typing import Dict, List, Optional
from router.domain import CapabilityMetadata, CapabilityType


class CapabilityRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._capabilities: Dict[str, CapabilityMetadata] = {}
        self._register_default_capabilities()

    def _register_default_capabilities(self):
        """Registers built-in platform capabilities into registry."""
        defaults = [
            CapabilityMetadata(
                capability_id="cap_retrieval_vector",
                name="Vector Embeddings Dense Retriever",
                type=CapabilityType.RETRIEVAL_VECTOR,
                cost_per_call=0.0005,
                est_latency_ms=120.0,
                required_permissions=["workspace:read"],
                description="Dense semantic vector similarity search across document chunks"
            ),
            CapabilityMetadata(
                capability_id="cap_retrieval_bm25",
                name="BM25 Sparse Keyword Retriever",
                type=CapabilityType.RETRIEVAL_BM25,
                cost_per_call=0.0002,
                est_latency_ms=45.0,
                required_permissions=["workspace:read"],
                description="Lexical sparse keyword search using BM25 scoring algorithm"
            ),
            CapabilityMetadata(
                capability_id="cap_text_to_sql",
                name="Text-to-SQL AST Synthesizer",
                type=CapabilityType.TEXT_TO_SQL,
                cost_per_call=0.002,
                est_latency_ms=350.0,
                required_permissions=["workspace:read"],
                description="Introspects SQL schema, generates read-only SELECT queries, and enforces AST bounds"
            ),
            CapabilityMetadata(
                capability_id="cap_analytics_engine",
                name="SQL Data Aggregation Analytics Engine",
                type=CapabilityType.ANALYTICS_ENGINE,
                cost_per_call=0.001,
                est_latency_ms=200.0,
                required_permissions=["workspace:read"],
                description="Executes statistical aggregation, trend analysis, and numerical computations on tabular data"
            ),
            CapabilityMetadata(
                capability_id="cap_document_summarizer",
                name="Multi-Document Summarizer",
                type=CapabilityType.DOCUMENT_SUMMARIZER,
                cost_per_call=0.0015,
                est_latency_ms=300.0,
                required_permissions=["workspace:read"],
                description="Synthesizes long-form document excerpts into structured executive summaries"
            ),
            CapabilityMetadata(
                capability_id="cap_hitl_approval_gate",
                name="Human-in-the-Loop Operator Review Gate",
                type=CapabilityType.HUMAN_APPROVAL,
                cost_per_call=0.0,
                est_latency_ms=0.0,
                required_permissions=["workspace:read"],
                description="Freezes workflow and generates human operator approval ticket"
            ),
        ]
        for cap in defaults:
            self.register_capability(cap)

    def register_capability(self, capability: CapabilityMetadata):
        """Registers a new capability into the registry."""
        with self._lock:
            self._capabilities[capability.capability_id] = capability

    def get_capability(self, capability_id: str) -> Optional[CapabilityMetadata]:
        with self._lock:
            return self._capabilities.get(capability_id)

    def list_capabilities(self, enabled_only: bool = True) -> List[CapabilityMetadata]:
        with self._lock:
            caps = list(self._capabilities.values())
            if enabled_only:
                caps = [c for c in caps if c.enabled]
            return caps

    def get_capabilities_by_type(self, cap_type: CapabilityType) -> List[CapabilityMetadata]:
        with self._lock:
            return [c for c in self._capabilities.values() if c.type == cap_type and c.enabled]
