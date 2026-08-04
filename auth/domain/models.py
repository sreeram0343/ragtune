"""
RAGTUNE Enterprise Identity & Access Management - Core Domain Models
Defines domain entities, lifecycle states, and context objects.
"""

from datetime import datetime, UTC
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from auth.domain.permissions import OrgRole, Permission, WorkspaceRole


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class UserStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING_ACTIVATION = "PENDING_ACTIVATION"


class OrgStatus(StrEnum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class InvitationStatus(StrEnum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class UserDomain(BaseModel):
    user_id: str
    email: str
    password_hash: str
    full_name: str
    is_email_verified: bool = False
    status: UserStatus = UserStatus.ACTIVE
    failed_login_attempts: int = 0
    locked_until: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class OrganizationDomain(BaseModel):
    org_id: str
    name: str
    slug: str
    domain: str | None = None
    status: OrgStatus = OrgStatus.ACTIVE
    tier: str = "ENTERPRISE"
    created_at: datetime = Field(default_factory=utc_now)


class WorkspaceDomain(BaseModel):
    workspace_id: str
    org_id: str
    name: str
    slug: str
    created_at: datetime = Field(default_factory=utc_now)


class ProjectDomain(BaseModel):
    project_id: str
    workspace_id: str
    name: str
    created_at: datetime = Field(default_factory=utc_now)


class OrganizationMemberDomain(BaseModel):
    org_id: str
    user_id: str
    role: OrgRole = OrgRole.MEMBER
    joined_at: datetime = Field(default_factory=utc_now)


class WorkspaceMemberDomain(BaseModel):
    workspace_id: str
    user_id: str
    role: WorkspaceRole = WorkspaceRole.MEMBER
    joined_at: datetime = Field(default_factory=utc_now)


class SessionDomain(BaseModel):
    session_id: str
    user_id: str
    refresh_token_hash: str
    ip_address: str | None = None
    user_agent: str | None = None
    is_revoked: bool = False
    expires_at: datetime
    created_at: datetime = Field(default_factory=utc_now)
    last_active_at: datetime = Field(default_factory=utc_now)


class InvitationDomain(BaseModel):
    invitation_id: str
    email: str
    org_id: str
    workspace_id: str | None = None
    role: str
    token_hash: str
    status: InvitationStatus = InvitationStatus.PENDING
    expires_at: datetime
    created_at: datetime = Field(default_factory=utc_now)


class AuditEventDomain(BaseModel):
    event_id: str
    tenant_id: str = "default"
    org_id: str | None = None
    workspace_id: str | None = None
    actor_id: str
    event_type: str
    resource_type: str
    resource_id: str | None = None
    status: str = "SUCCESS"
    ip_address: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=utc_now)


class SecurityContext(BaseModel):
    """Context extracted from request token and attached to request pipeline."""

    user_id: str
    email: str
    status: UserStatus
    org_id: str | None = None
    org_role: OrgRole | None = None
    workspace_id: str | None = None
    workspace_role: WorkspaceRole | None = None
    permissions: list[Permission] = Field(default_factory=list)
    session_id: str | None = None
    ip_address: str | None = None

    def has_permission(self, perm: Permission) -> bool:
        return perm in self.permissions
