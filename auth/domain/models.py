"""
RAGTUNE Enterprise Identity & Access Management - Core Domain Models
Defines domain entities, lifecycle states, and context objects.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, EmailStr
from auth.domain.permissions import OrgRole, WorkspaceRole, Permission


class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    PENDING_ACTIVATION = "PENDING_ACTIVATION"


class OrgStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class InvitationStatus(str, Enum):
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
    locked_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class OrganizationDomain(BaseModel):
    org_id: str
    name: str
    slug: str
    domain: Optional[str] = None
    status: OrgStatus = OrgStatus.ACTIVE
    tier: str = "ENTERPRISE"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceDomain(BaseModel):
    workspace_id: str
    org_id: str
    name: str
    slug: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectDomain(BaseModel):
    project_id: str
    workspace_id: str
    name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrganizationMemberDomain(BaseModel):
    org_id: str
    user_id: str
    role: OrgRole = OrgRole.MEMBER
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceMemberDomain(BaseModel):
    workspace_id: str
    user_id: str
    role: WorkspaceRole = WorkspaceRole.MEMBER
    joined_at: datetime = Field(default_factory=datetime.utcnow)


class SessionDomain(BaseModel):
    session_id: str
    user_id: str
    refresh_token_hash: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_revoked: bool = False
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active_at: datetime = Field(default_factory=datetime.utcnow)


class InvitationDomain(BaseModel):
    invitation_id: str
    email: str
    org_id: str
    workspace_id: Optional[str] = None
    role: str
    token_hash: str
    status: InvitationStatus = InvitationStatus.PENDING
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditEventDomain(BaseModel):
    event_id: str
    tenant_id: str = "default"
    org_id: Optional[str] = None
    workspace_id: Optional[str] = None
    actor_id: str
    event_type: str
    resource_type: str
    resource_id: Optional[str] = None
    status: str = "SUCCESS"
    ip_address: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SecurityContext(BaseModel):
    """Context extracted from request token and attached to request pipeline."""
    user_id: str
    email: str
    status: UserStatus
    org_id: Optional[str] = None
    org_role: Optional[OrgRole] = None
    workspace_id: Optional[str] = None
    workspace_role: Optional[WorkspaceRole] = None
    permissions: List[Permission] = Field(default_factory=list)
    session_id: Optional[str] = None
    ip_address: Optional[str] = None

    def has_permission(self, perm: Permission) -> bool:
        return perm in self.permissions
