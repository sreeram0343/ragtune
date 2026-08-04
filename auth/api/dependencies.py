"""
RAGTUNE Enterprise Identity & Access Management - FastAPI Dependencies
Injects security context, validates Bearer tokens, and enforces RBAC permission guards.
"""

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.domain.models import SecurityContext, UserStatus
from auth.domain.permissions import OrgRole, Permission, WorkspaceRole
from auth.security.jwt_handler import JWTHandler
from auth.services.authorization_service import AuthorizationService
from auth.storage.auth_db import AuthDatabaseRepository

bearer_scheme = HTTPBearer(auto_error=False)
jwt_handler = JWTHandler()
auth_db = AuthDatabaseRepository()
authz_service = AuthorizationService()


def get_security_context(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> SecurityContext:
    """
    FastAPI dependency extracting and validating Bearer access token into SecurityContext.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401, detail="Authentication credentials (Bearer token) required"
        )

    token = credentials.credentials
    is_valid, claims, msg = jwt_handler.decode_access_token(token)

    if not is_valid or not claims:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {msg}")

    user_id = claims.get("sub")
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(status_code=401, detail="Invalid token claims: sub missing or invalid")
    user = auth_db.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User account not found")

    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(status_code=403, detail="User account has been suspended")

    org_role = OrgRole(claims["org_role"]) if claims.get("org_role") else None
    ws_role = WorkspaceRole(claims["ws_role"]) if claims.get("ws_role") else None

    effective_perms = authz_service.get_effective_permissions(org_role, ws_role)

    client_ip = request.client.host if request.client else None

    return SecurityContext(
        user_id=user.user_id,
        email=user.email,
        status=user.status,
        org_id=claims.get("org_id"),
        org_role=org_role,
        workspace_id=claims.get("ws_id"),
        workspace_role=ws_role,
        permissions=effective_perms,
        session_id=claims.get("sid"),
        ip_address=client_ip,
    )


def require_permission(perm: Permission) -> Callable:
    """
    Dependency factory enforcing that the authenticated caller has the specified permission.
    """

    def permission_checker(
        ctx: SecurityContext = Depends(get_security_context),
    ) -> SecurityContext:
        if not authz_service.evaluate_permission(ctx, perm):
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: Action requires permission '{perm.value}'",
            )
        return ctx

    return permission_checker
