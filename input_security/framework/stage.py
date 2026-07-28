"""
RAGTUNE Input Security Pipeline - Core Framework & Data Models
Defines abstract security stage interfaces, telemetry containers, and trust levels.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from auth.domain.models import SecurityContext


class TrustLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNTRUSTED = "UNTRUSTED"


class StageResult(BaseModel):
    stage_id: int
    stage_name: str
    passed: bool
    threat_score: float = 0.0  # 0.0 to 100.0
    sanitized_payload: Dict[str, Any] = Field(default_factory=dict)
    audit_notes: List[str] = Field(default_factory=list)
    error_detail: Optional[str] = None
    execution_time_ms: float = 0.0


class SecurityRequestContainer(BaseModel):
    raw_body: bytes = b""
    headers: Dict[str, str] = Field(default_factory=dict)
    client_ip: Optional[str] = None
    path: str = ""
    method: str = "POST"
    user_context: Optional[SecurityContext] = None
    parsed_payload: Dict[str, Any] = Field(default_factory=dict)
    user_query: Optional[str] = None


class EnrichedSecurityRequest(BaseModel):
    request_id: str
    original_container: SecurityRequestContainer
    sanitized_query: str = ""
    sanitized_payload: Dict[str, Any] = Field(default_factory=dict)
    security_context: Optional[SecurityContext] = None
    trust_level: TrustLevel = TrustLevel.HIGH
    cumulative_risk_score: float = 0.0
    stage_evaluations: List[StageResult] = Field(default_factory=list)
    total_latency_ms: float = 0.0
    cleared_for_orchestration: bool = False


class SecurityViolationException(Exception):
    def __init__(self, message: str, status_code: int = 400, stage_name: Optional[str] = None, risk_score: float = 0.0):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.stage_name = stage_name
        self.risk_score = risk_score


class BaseSecurityStage(ABC):
    def __init__(self, stage_id: int, stage_name: str):
        self.stage_id = stage_id
        self.stage_name = stage_name

    @abstractmethod
    def process(self, container: SecurityRequestContainer) -> StageResult:
        """Executes stage validation and returns StageResult."""
        pass
