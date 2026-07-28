"""
RAGTUNE Enterprise Identity & Access Management - Authorization & RBAC Evaluator
Evaluates user role permissions across Organizations and Workspaces.
"""

from typing import List, Set, Optional
from auth.domain.permissions import (
    OrgRole, WorkspaceRole, Permission,
    ORG_ROLE_PERMISSIONS, WORKSPACE_ROLE_PERMISSIONS
)
from auth.domain.models import SecurityContext, UserStatus


class AuthorizationService:
    def get_effective_permissions(
        self, org_role: Optional[OrgRole] = None, workspace_role: Optional[WorkspaceRole] = None
    ) -> List[Permission]:
        """
        Calculates union set of effective permissions granted by Org Role and Workspace Role.
        """
        perms: Set[Permission] = set()

        if org_role and org_role in ORG_ROLE_PERMISSIONS:
            perms.update(ORG_ROLE_PERMISSIONS[org_role])

        if workspace_role and workspace_role in WORKSPACE_ROLE_PERMISSIONS:
            perms.update(WORKSPACE_ROLE_PERMISSIONS[workspace_role])

        return list(perms)

    def evaluate_permission(
        self, ctx: SecurityContext, required_permission: Permission
    ) -> bool:
        """
        Validates if SecurityContext grants required permission.
        """
        if ctx.status == UserStatus.SUSPENDED:
            return False

        # Org Owner has implicit override access to all permissions
        if ctx.org_role == OrgRole.OWNER:
            return True

        return required_permission in ctx.permissions
