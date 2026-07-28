"""
RAGTUNE Intent Router & Query Planning Engine - Core Domain Models
Defines intent categories, planning strategies, capability types, and metadata schemas.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class IntentCategory(str, Enum):
    STRUCTURED_SQL = "STRUCTURED_SQL"
    UNSTRUCTURED_RAG = "UNSTRUCTURED_RAG"
    HYBRID_ANALYTICS = "HYBRID_ANALYTICS"
    POLICY_LOOKUP = "POLICY_LOOKUP"
    SUMMARIZATION = "SUMMARIZATION"
    RESEARCH = "RESEARCH"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    UNKNOWN = "UNKNOWN"


class PlanningStrategy(str, Enum):
    LOW_LATENCY = "LOW_LATENCY"
    BALANCED = "BALANCED"
    MAX_ACCURACY = "MAX_ACCURACY"
    COST_MINIMIZED = "COST_MINIMIZED"


class CapabilityType(str, Enum):
    RETRIEVAL_VECTOR = "RETRIEVAL_VECTOR"
    RETRIEVAL_BM25 = "RETRIEVAL_BM25"
    TEXT_TO_SQL = "TEXT_TO_SQL"
    ANALYTICS_ENGINE = "ANALYTICS_ENGINE"
    DOCUMENT_SUMMARIZER = "DOCUMENT_SUMMARIZER"
    WEB_SEARCH = "WEB_SEARCH"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


class CapabilityMetadata(BaseModel):
    capability_id: str
    name: str
    type: CapabilityType
    cost_per_call: float = 0.001  # USD
    est_latency_ms: float = 150.0  # milliseconds
    required_permissions: List[str] = Field(default_factory=list)
    description: str = ""
    enabled: bool = True
