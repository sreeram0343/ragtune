"""
RAGTUNE Input Security Pipeline - Stage 2: Authentication & Session Verification
Validates Bearer access token, DB session, and active user account status.
"""

import time

from auth.domain.models import SecurityContext, UserStatus
from auth.domain.permissions import OrgRole, WorkspaceRole
from auth.security.jwt_handler import JWTHandler
from auth.services.authorization_service import AuthorizationService
from auth.storage.auth_db import AuthDatabaseRepository
from input_security.framework.stage import (
    BaseSecurityStage,
    SecurityRequestContainer,
    SecurityViolationException,
    StageResult,
)

# Endpoints exempt from mandatory Bearer authentication (public endpoints)
PUBLIC_EXEMPT_PATHS = [
    "/health",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/invitations/accept",
    "/static",
    "/",
]


class AuthVerificationStage(BaseSecurityStage):
    def __init__(self, db_repo: AuthDatabaseRepository):
        super().__init__(stage_id=2, stage_name="Authentication & Session Verification")
        self.jwt_handler = JWTHandler()
        self.db = db_repo
        self.authz = AuthorizationService()

    def process(self, container: SecurityRequestContainer) -> StageResult:
        t0 = time.time()
        audit_notes = []

        # Check if path is exempt from authentication
        path_clean = container.path.split("?")[0]
        if any(path_clean.startswith(p) for p in PUBLIC_EXEMPT_PATHS):
            audit_notes.append(
                f"Path '{path_clean}' is exempt from mandatory authentication"
            )
            return StageResult(
                stage_id=self.stage_id,
                stage_name=self.stage_name,
                passed=True,
                threat_score=0.0,
                sanitized_payload=container.parsed_payload,
                audit_notes=audit_notes,
                execution_time_ms=round((time.time() - t0) * 1000, 2),
            )

        # Extract Authorization header
        auth_header = container.headers.get("authorization") or container.headers.get(
            "Authorization"
        )
        if not auth_header or not auth_header.startswith("Bearer "):
            raise SecurityViolationException(
                message="Authentication credentials (Bearer token) required",
                status_code=401,
                stage_name=self.stage_name,
                risk_score=100.0,
            )

        token = auth_header.replace("Bearer ", "").strip()
        is_valid, claims, msg = self.jwt_handler.decode_access_token(token)

        if not is_valid or not claims:
            raise SecurityViolationException(
                message=f"Authentication token verification failed: {msg}",
                status_code=401,
                stage_name=self.stage_name,
                risk_score=90.0,
            )

        user_id = claims.get("sub")
        if not user_id or not isinstance(user_id, str):
            raise SecurityViolationException(
                message="Invalid token claims: sub missing or invalid",
                status_code=401,
                stage_name=self.stage_name,
                risk_score=90.0,
            )
        user = self.db.get_user_by_id(user_id)

        if not user:
            raise SecurityViolationException(
                message="Authenticated user account not found in database",
                status_code=401,
                stage_name=self.stage_name,
                risk_score=100.0,
            )

        if user.status == UserStatus.SUSPENDED:
            raise SecurityViolationException(
                message="User account has been administratively suspended",
                status_code=403,
                stage_name=self.stage_name,
                risk_score=100.0,
            )

        org_role = OrgRole(claims["org_role"]) if claims.get("org_role") else None
        ws_role = WorkspaceRole(claims["ws_role"]) if claims.get("ws_role") else None

        effective_perms = self.authz.get_effective_permissions(org_role, ws_role)

        sec_ctx = SecurityContext(
            user_id=user.user_id,
            email=user.email,
            status=user.status,
            org_id=claims.get("org_id"),
            org_role=org_role,
            workspace_id=claims.get("ws_id"),
            workspace_role=ws_role,
            permissions=effective_perms,
            session_id=claims.get("sid"),
            ip_address=container.client_ip,
        )

        container.user_context = sec_ctx
        audit_notes.append(f"Authenticated user '{user.user_id}' ({user.email})")

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
