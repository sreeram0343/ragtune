"""
RAGTUNE Input Security Pipeline - Stage 3: Multi-Tenant RBAC Authorization
Validates tenant boundaries, Org/Workspace roles, and fine-grained permissions.
"""

import time

from auth.domain.permissions import Permission
from auth.services.authorization_service import AuthorizationService
from input_security.framework.stage import (
    BaseSecurityStage,
    SecurityRequestContainer,
    SecurityViolationException,
    StageResult,
)

# Map endpoint paths to required permissions
PATH_PERMISSION_MAP: dict[str, Permission] = {
    "/api/v1/auth/invitations": Permission.ORG_MANAGE_MEMBERS,
    "/api/v1/auth/audit-logs": Permission.AUDIT_READ,
    "/api/v1/auth/admin/users": Permission.USER_SUSPEND,
    "/api/v1/ingest/text": Permission.WORKSPACE_WRITE,
}


class RBACAuthorizationStage(BaseSecurityStage):
    def __init__(self):
        super().__init__(stage_id=3, stage_name="Multi-Tenant RBAC Authorization")
        self.authz = AuthorizationService()

    def process(self, container: SecurityRequestContainer) -> StageResult:
        t0 = time.time()
        audit_notes = []

        ctx = container.user_context
        # If no user context (e.g. public endpoint cleared in Stage 2), pass
        if not ctx:
            audit_notes.append("No security context attached (Public Endpoint)")
            return StageResult(
                stage_id=self.stage_id,
                stage_name=self.stage_name,
                passed=True,
                threat_score=0.0,
                sanitized_payload=container.parsed_payload,
                audit_notes=audit_notes,
                execution_time_ms=round((time.time() - t0) * 1000, 2),
            )

        # Determine required permission for path
        path_clean = container.path.split("?")[0]
        required_perm: Permission | None = None
        for prefix, perm in PATH_PERMISSION_MAP.items():
            if path_clean.startswith(prefix):
                required_perm = perm
                break

        if required_perm:
            if not self.authz.evaluate_permission(ctx, required_perm):
                raise SecurityViolationException(
                    message=f"Forbidden: Action on path '{path_clean}' requires permission '{required_perm.value}'",
                    status_code=403,
                    stage_name=self.stage_name,
                    risk_score=90.0,
                )
            audit_notes.append(
                f"Granted permission '{required_perm.value}' for path '{path_clean}'"
            )

        latency = (time.time() - t0) * 1000
        return StageResult(
            stage_id=self.stage_id,
            stage_name=self.stage_name,
            passed=True,
            threat_score=0.0,
            sanitized_payload=container.parsed_payload,
            audit_notes=audit_notes,
            execution_time_ms=round(latency, 2),
        )
