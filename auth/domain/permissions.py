"""
RAGTUNE Enterprise Identity & Access Management - Permissions & RBAC Matrix
Defines system roles, permission scopes, and RBAC evaluation matrices.
"""

from enum import StrEnum


class OrgRole(StrEnum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
    GUEST = "GUEST"


class WorkspaceRole(StrEnum):
    WORKSPACE_ADMIN = "WORKSPACE_ADMIN"
    MEMBER = "MEMBER"
    VIEWER = "VIEWER"


class Permission(StrEnum):
    # Organization Permissions
    ORG_READ = "org:read"
    ORG_WRITE = "org:write"
    ORG_DELETE = "org:delete"
    ORG_MANAGE_MEMBERS = "org:manage_members"

    # Workspace Permissions
    WORKSPACE_READ = "workspace:read"
    WORKSPACE_WRITE = "workspace:write"
    WORKSPACE_DELETE = "workspace:delete"
    WORKSPACE_MANAGE_MEMBERS = "workspace:manage_members"

    # Project Permissions
    PROJECT_READ = "project:read"
    PROJECT_WRITE = "project:write"
    PROJECT_DELETE = "project:delete"

    # Admin & Security Permissions
    USER_MANAGE = "user:manage"
    USER_SUSPEND = "user:suspend"
    SECURITY_ADMIN = "security:admin"
    AUDIT_READ = "audit:read"


# Organization Role Permission Map
ORG_ROLE_PERMISSIONS: dict[OrgRole, set[Permission]] = {
    OrgRole.OWNER: {
        Permission.ORG_READ,
        Permission.ORG_WRITE,
        Permission.ORG_DELETE,
        Permission.ORG_MANAGE_MEMBERS,
        Permission.WORKSPACE_READ,
        Permission.WORKSPACE_WRITE,
        Permission.WORKSPACE_DELETE,
        Permission.WORKSPACE_MANAGE_MEMBERS,
        Permission.PROJECT_READ,
        Permission.PROJECT_WRITE,
        Permission.PROJECT_DELETE,
        Permission.USER_MANAGE,
        Permission.USER_SUSPEND,
        Permission.SECURITY_ADMIN,
        Permission.AUDIT_READ,
    },
    OrgRole.ADMIN: {
        Permission.ORG_READ,
        Permission.ORG_WRITE,
        Permission.ORG_MANAGE_MEMBERS,
        Permission.WORKSPACE_READ,
        Permission.WORKSPACE_WRITE,
        Permission.WORKSPACE_DELETE,
        Permission.WORKSPACE_MANAGE_MEMBERS,
        Permission.PROJECT_READ,
        Permission.PROJECT_WRITE,
        Permission.PROJECT_DELETE,
        Permission.USER_MANAGE,
        Permission.AUDIT_READ,
    },
    OrgRole.MEMBER: {
        Permission.ORG_READ,
        Permission.WORKSPACE_READ,
        Permission.WORKSPACE_WRITE,
        Permission.PROJECT_READ,
        Permission.PROJECT_WRITE,
    },
    OrgRole.GUEST: {
        Permission.ORG_READ,
        Permission.WORKSPACE_READ,
        Permission.PROJECT_READ,
    },
}

# Workspace Role Permission Map
WORKSPACE_ROLE_PERMISSIONS: dict[WorkspaceRole, set[Permission]] = {
    WorkspaceRole.WORKSPACE_ADMIN: {
        Permission.WORKSPACE_READ,
        Permission.WORKSPACE_WRITE,
        Permission.WORKSPACE_DELETE,
        Permission.WORKSPACE_MANAGE_MEMBERS,
        Permission.PROJECT_READ,
        Permission.PROJECT_WRITE,
        Permission.PROJECT_DELETE,
    },
    WorkspaceRole.MEMBER: {
        Permission.WORKSPACE_READ,
        Permission.PROJECT_READ,
        Permission.PROJECT_WRITE,
    },
    WorkspaceRole.VIEWER: {
        Permission.WORKSPACE_READ,
        Permission.PROJECT_READ,
    },
}
