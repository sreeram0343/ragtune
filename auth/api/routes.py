"""
RAGTUNE Enterprise Identity & Access Management - REST API Router
Defines endpoints for Authentication, Token Rotation, Organizations, Invitations, Audit Logs, and Admin controls.
"""

from fastapi import APIRouter, Depends, HTTPException, Request

from auth.api.dependencies import get_security_context, require_permission
from auth.api.schemas import (
    AcceptInvitationRequest,
    CreateInvitationRequest,
    CreateOrgRequest,
    LoginRequest,
    PasswordChangeRequest,
    RefreshTokenRequest,
    RegisterUserRequest,
    TokenResponse,
)
from auth.domain.models import SecurityContext
from auth.domain.permissions import Permission
from auth.services.audit_service import AuditService
from auth.services.identity_service import IdentityService
from auth.services.organization_service import OrganizationService
from auth.services.token_service import TokenService
from auth.storage.auth_db import AuthDatabaseRepository

router = APIRouter(prefix="/api/v1/auth", tags=["Identity & Access Management"])

# Singletons for API router
db_repo = AuthDatabaseRepository()
audit_service = AuditService(db_repo)
token_service = TokenService(db_repo)
identity_service = IdentityService(db_repo, token_service, audit_service)
org_service = OrganizationService(db_repo, audit_service)


@router.post("/register", status_code=201)
def register(payload: RegisterUserRequest, request: Request):
    """Registers a new enterprise user account."""
    client_ip = request.client.host if request.client else None
    success, user, msg = identity_service.register_user(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        ip_address=client_ip,
    )
    if not success or not user:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "user_id": user.user_id, "email": user.email}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request):
    """Authenticates user credentials and issues Access + Refresh Tokens."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    success, data, msg = identity_service.authenticate_user(
        email=payload.email,
        password=payload.password,
        ip_address=client_ip,
        user_agent=user_agent,
    )
    if not success:
        raise HTTPException(status_code=401, detail=msg)
    return data


@router.post("/refresh")
def refresh_token(payload: RefreshTokenRequest, request: Request):
    """Rotates refresh token (RTR) and issues a fresh token pair."""
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    success, new_access, new_refresh, msg = token_service.rotate_refresh_token(
        refresh_token=payload.refresh_token, ip_address=client_ip, user_agent=user_agent
    )
    if not success:
        raise HTTPException(status_code=401, detail=msg)

    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "Bearer",  # nosec B105
        "expires_in": 900,
    }


@router.post("/logout")
def logout(ctx: SecurityContext = Depends(get_security_context)):
    """Revokes the current active session."""
    if ctx.session_id:
        token_service.revoke_session(ctx.session_id)
        audit_service.log_event(
            actor_id=ctx.user_id,
            event_type="USER_LOGOUT",
            resource_type="SESSION",
            resource_id=ctx.session_id,
            ip_address=ctx.ip_address,
        )
    return {"message": "Logged out successfully"}


@router.post("/logout-all")
def logout_all(ctx: SecurityContext = Depends(get_security_context)):
    """Revokes all active sessions for the current user across all devices."""
    token_service.revoke_all_sessions(ctx.user_id)
    audit_service.log_event(
        actor_id=ctx.user_id,
        event_type="USER_LOGOUT_ALL",
        resource_type="USER",
        resource_id=ctx.user_id,
        ip_address=ctx.ip_address,
    )
    return {"message": "All sessions revoked successfully across all devices"}


@router.get("/me")
def get_current_user_profile(ctx: SecurityContext = Depends(get_security_context)):
    """Returns profile and active security context claims."""
    user = db_repo.get_user_by_id(ctx.user_id)
    if not user:
        raise HTTPException(status_code=44, detail="User not found")
    return {
        "user_id": user.user_id,
        "email": user.email,
        "full_name": user.full_name,
        "status": user.status.value,
        "org_id": ctx.org_id,
        "org_role": ctx.org_role.value if ctx.org_role else None,
        "workspace_id": ctx.workspace_id,
        "workspace_role": ctx.workspace_role.value if ctx.workspace_role else None,
        "permissions": [p.value for p in ctx.permissions],
    }


@router.post("/password/change")
def change_password(
    payload: PasswordChangeRequest, ctx: SecurityContext = Depends(get_security_context)
):
    """Changes user password and invalidates all active sessions."""
    success, msg = identity_service.change_password(
        user_id=ctx.user_id,
        old_password=payload.old_password,
        new_password=payload.new_password,
        ip_address=ctx.ip_address,
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.post("/organizations", status_code=201)
def create_organization(
    payload: CreateOrgRequest, ctx: SecurityContext = Depends(get_security_context)
):
    """Creates a new Organization and default Workspace."""
    success, org, ws, msg = org_service.create_organization(
        creator_user_id=ctx.user_id, name=payload.name, domain=payload.domain
    )
    if not success or not org or not ws:
        raise HTTPException(status_code=400, detail=msg)

    return {
        "message": msg,
        "organization": org.model_dump(),
        "default_workspace": ws.model_dump(),
    }


@router.post("/invitations", status_code=201)
def issue_invitation(
    payload: CreateInvitationRequest,
    ctx: SecurityContext = Depends(require_permission(Permission.ORG_MANAGE_MEMBERS)),
):
    """Issues an invitation token to join Organization/Workspace."""
    if not ctx.org_id:
        raise HTTPException(
            status_code=400, detail="Organization context required to issue invitations"
        )

    success, raw_token, msg = org_service.create_invitation(
        sender_user_id=ctx.user_id,
        org_id=ctx.org_id,
        target_email=payload.target_email,
        role=payload.role,
        workspace_id=payload.workspace_id,
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"message": msg, "invitation_token": raw_token}


@router.post("/invitations/accept")
def accept_invitation(
    payload: AcceptInvitationRequest,
    ctx: SecurityContext = Depends(get_security_context),
):
    """Accepts an invitation token."""
    success, msg = org_service.accept_invitation(
        accepting_user_id=ctx.user_id, raw_token=payload.invitation_token
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 50,
    ctx: SecurityContext = Depends(require_permission(Permission.AUDIT_READ)),
):
    """Queries security audit log events."""
    logs = audit_service.query_audit_logs(limit=limit)
    return {"events": [log.model_dump() for log in logs]}


@router.post("/admin/users/{target_user_id}/suspend")
def suspend_user(
    target_user_id: str,
    ctx: SecurityContext = Depends(require_permission(Permission.USER_SUSPEND)),
):
    """Administratively suspends a user account and revokes all active sessions."""
    success, msg = identity_service.suspend_user(
        admin_actor_id=ctx.user_id,
        target_user_id=target_user_id,
        ip_address=ctx.ip_address,
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}
