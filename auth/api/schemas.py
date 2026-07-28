"""
RAGTUNE Enterprise Identity & Access Management - API Schemas
Pydantic v2 Data Transfer Objects for Auth & IAM REST Endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr


class RegisterUserRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 chars)")
    full_name: str = Field(..., min_length=2, description="User full name")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh Token string")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 900
    user: Dict[str, Any]


class PasswordChangeRequest(BaseModel):
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 chars)")


class CreateOrgRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Organization name")
    domain: Optional[str] = Field(None, description="Optional corporate domain")


class CreateWorkspaceRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Workspace name")


class CreateInvitationRequest(BaseModel):
    target_email: EmailStr = Field(..., description="Invitee email address")
    role: str = Field("MEMBER", description="Role to grant: OWNER, ADMIN, MEMBER, GUEST")
    workspace_id: Optional[str] = Field(None, description="Optional specific workspace ID")


class AcceptInvitationRequest(BaseModel):
    invitation_token: str = Field(..., description="Invitation raw token string")


class AuditQueryResponse(BaseModel):
    events: List[Dict[str, Any]]
