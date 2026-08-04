"""
RAGTUNE - Guardrail Layer 4: RBAC & Tenant Data Isolation Guard
Validates user permissions and enforces tenant-level data segregation.
"""

from security.rbac import Permission, UserContext


class RBACIsolationGuard:
    def evaluate_query_permission(
        self, user_context: UserContext, action_type: str = "QUERY_KNOWLEDGE"
    ) -> tuple[bool, float, str]:
        """
        Validates if user context permits the requested action type.
        """
        try:
            perm = Permission(action_type)
        except ValueError:
            perm = Permission.QUERY_KNOWLEDGE

        if not user_context.has_permission(perm):
            return (
                False,
                0.0,
                f"Role '{user_context.role.value}' does not possess required permission '{perm.value}'",
            )

        return (
            True,
            1.0,
            f"Access authorized for user '{user_context.user_id}' (Role: {user_context.role.value})",
        )

    def evaluate_table_access(
        self, user_context: UserContext, tables: list[str]
    ) -> tuple[bool, float, str]:
        """
        Validates whether target database tables match user RBAC restrictions.
        """
        denied_tables = []
        for table in tables:
            if not user_context.can_access_table(table):
                denied_tables.append(table)

        if denied_tables:
            return (
                False,
                0.0,
                f"Access denied to table(s): {', '.join(denied_tables)} under tenant '{user_context.tenant_id}'",
            )

        return (
            True,
            1.0,
            f"Table access authorized for tenant '{user_context.tenant_id}'",
        )
