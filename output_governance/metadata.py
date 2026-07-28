"""
RAGTUNE Output Security & Response Governance Engine - Metadata Generator
Synthesizes enterprise telemetry metadata, execution latency breakdowns, and audit references.
"""

import uuid
from typing import Optional
from output_governance.domain import GovernanceMetadata
from input_security.framework.stage import EnrichedSecurityRequest


class MetadataGenerator:
    def generate_metadata(
        self,
        security_request: EnrichedSecurityRequest,
        total_latency_ms: float,
        quality_score: float = 1.0,
        citation_count: int = 0
    ) -> GovernanceMetadata:
        """
        Builds GovernanceMetadata container for output API response.
        """
        sec_ctx = security_request.security_context
        tenant_id = sec_ctx.org_id if sec_ctx and sec_ctx.org_id else "global_tenant"
        workspace_id = sec_ctx.workspace_id if sec_ctx and sec_ctx.workspace_id else "global_ws"
        audit_ref = f"audit_ref_{uuid.uuid4().hex[:12]}"

        return GovernanceMetadata(
            request_id=security_request.request_id,
            workflow_id=f"wf_{uuid.uuid4().hex[:8]}",
            tenant_id=tenant_id,
            workspace_id=workspace_id,
            total_latency_ms=round(total_latency_ms, 2),
            est_cost_usd=0.0015,
            quality_score=quality_score,
            citation_count=citation_count,
            audit_reference_id=audit_ref
        )
