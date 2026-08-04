"""
RAGTUNE Output Security & Response Governance Engine - Domain Models
Defines policy decisions, redaction records, governance metadata, and API envelope models.
"""

from enum import StrEnum

from pydantic import BaseModel, Field


class PolicyDecision(StrEnum):
    ALLOW = "ALLOW"
    WARN_AND_ALLOW = "WARN_AND_ALLOW"
    BLOCK = "BLOCK"


class RedactionRecord(BaseModel):
    field_name: str
    data_type: str  # "EMAIL", "PHONE", "SSN", "API_KEY", "PASSWORD", "FINANCIAL"
    masked_placeholder: str
    count: int = 1


class GovernanceMetadata(BaseModel):
    request_id: str
    workflow_id: str
    tenant_id: str = "global_tenant"
    workspace_id: str = "global_ws"
    total_latency_ms: float = 0.0
    est_cost_usd: float = 0.0
    quality_score: float = 1.0
    citation_count: int = 0
    audit_reference_id: str = ""


class GovernedResponseEnvelope(BaseModel):
    governed_id: str
    status: str = "SUCCESS"
    formatted_content: str
    original_format: str = "MARKDOWN"
    redactions: list[RedactionRecord] = Field(default_factory=list)
    metadata: GovernanceMetadata
    policy_decision: PolicyDecision = PolicyDecision.ALLOW
    explanation: str = ""
