"""
RAGTUNE Enterprise Verification & Quality Assurance Engine - Domain Models
Defines verification claims, reflection tokens, quality metrics, decision actions, and quality reports.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VerificationAction(str, Enum):
    APPROVE = "APPROVE"
    APPROVE_WITH_WARNING = "APPROVE_WITH_WARNING"
    REGENERATE = "REGENERATE"
    TRIGGER_CRAG_RE_RETRIEVAL = "TRIGGER_CRAG_RE_RETRIEVAL"
    ESCALATE_HITL = "ESCALATE_HITL"
    REJECT = "REJECT"


class VerificationClaim(BaseModel):
    claim_id: str
    statement_text: str
    is_grounded: bool = True
    supporting_citation_id: Optional[str] = None
    confidence: float = 1.0


class ReflectionToken(BaseModel):
    token_type: str  # "IS_SUPPORTED", "IS_RELEVANT", "UTILITY"
    score: float = 1.0
    rationale: str = ""


class QualityMetrics(BaseModel):
    groundedness_score: float = 1.0
    faithfulness_score: float = 1.0
    citation_coverage: float = 1.0
    relevance_score: float = 1.0
    hallucination_risk: float = 0.0
    overall_quality_score: float = 1.0
    verification_latency_ms: float = 0.0


class QualityReport(BaseModel):
    report_id: str
    natural_query: str
    response_narrative: str
    action: VerificationAction = VerificationAction.APPROVE
    quality_score: float = 1.0
    claims: List[VerificationClaim] = Field(default_factory=list)
    reflection_tokens: List[ReflectionToken] = Field(default_factory=list)
    metrics: QualityMetrics = Field(default_factory=QualityMetrics)
    explanation: str = ""
