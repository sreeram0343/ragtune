"""
RAGTUNE - Security and RBAC Module
Role-Based Access Control and Multi-Tenant Isolation.
"""

from enum import Enum
from typing import List, Set
from pydantic import BaseModel, Field


class Role(str, Enum):
    ADMIN = "ADMIN"
    ANALYST = "ANALYST"
    AUDITOR = "AUDITOR"
    VIEWER = "VIEWER"


class Permission(str, Enum):
    QUERY_KNOWLEDGE = "QUERY_KNOWLEDGE"
    EXECUTE_SQL = "EXECUTE_SQL"
    VIEW_PII = "VIEW_PII"
    APPROVE_HITL = "APPROVE_HITL"
    INGEST_DOCUMENTS = "INGEST_DOCUMENTS"
    ADMIN_CONFIG = "ADMIN_CONFIG"


ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.QUERY_KNOWLEDGE,
        Permission.EXECUTE_SQL,
        Permission.VIEW_PII,
        Permission.APPROVE_HITL,
        Permission.INGEST_DOCUMENTS,
        Permission.ADMIN_CONFIG,
    },
    Role.ANALYST: {
        Permission.QUERY_KNOWLEDGE,
        Permission.EXECUTE_SQL,
        Permission.APPROVE_HITL,
        Permission.INGEST_DOCUMENTS,
    },
    Role.AUDITOR: {
        Permission.QUERY_KNOWLEDGE,
        Permission.VIEW_PII,
    },
    Role.VIEWER: {
        Permission.QUERY_KNOWLEDGE,
    },
}


class UserContext(BaseModel):
    user_id: str = "usr_enterprise_01"
    role: Role = Role.ANALYST
    tenant_id: str = "tenant_enterprise_default"
    allowed_tables: List[str] = Field(default_factory=lambda: ["*"])

    def has_permission(self, permission: Permission) -> bool:
        """Check if user role grants the specified permission."""
        user_perms = ROLE_PERMISSIONS.get(self.role, set())
        return permission in user_perms

    def can_access_table(self, table_name: str) -> bool:
        """Verify if table access is allowed under current user context."""
        if "*" in self.allowed_tables:
            return True
        return table_name.lower() in [t.lower() for t in self.allowed_tables]


def get_default_user_context(role_str: str = "ANALYST", tenant_id: str = "tenant_enterprise_default") -> UserContext:
    """Helper to generate default security context."""
    try:
        role = Role(role_str.upper())
    except ValueError:
        role = Role.ANALYST
    return UserContext(
        user_id=f"user_{role.value.lower()}",
        role=role,
        tenant_id=tenant_id
    )
