"""
RAGTUNE Enterprise Identity & Access Management - Authorization & Multi-Tenancy Test Suite
"""

from auth.domain.models import SecurityContext, UserStatus
from auth.domain.permissions import OrgRole, Permission
from auth.services.audit_service import AuditService
from auth.services.authorization_service import AuthorizationService
from auth.services.identity_service import IdentityService
from auth.services.organization_service import OrganizationService
from auth.services.token_service import TokenService
from auth.storage.auth_db import AuthDatabaseRepository


def test_organization_and_invitation_flow():
    repo = AuthDatabaseRepository("sqlite:///:memory:")
    audit = AuditService(repo)
    token_svc = TokenService(repo)
    identity_svc = IdentityService(repo, token_svc, audit)
    org_svc = OrganizationService(repo, audit)

    # Register Owner and Invitee
    _, owner, _ = identity_svc.register_user(
        "owner@acme.com", "Password123!", "Acme Owner"
    )
    _, invitee, _ = identity_svc.register_user(
        "invitee@acme.com", "Password123!", "Acme Invitee"
    )

    # 1. Create Organization
    org_ok, org, ws, _ = org_svc.create_organization(owner.user_id, "Acme Corp")
    assert org_ok
    assert org is not None
    assert ws is not None

    # 2. Issue Invitation
    inv_ok, raw_token, _ = org_svc.create_invitation(
        sender_user_id=owner.user_id,
        org_id=org.org_id,
        target_email=invitee.email,
        role="MEMBER",
    )
    assert inv_ok
    assert raw_token is not None

    # 3. Accept Invitation
    accept_ok, _ = org_svc.accept_invitation(invitee.user_id, raw_token)
    assert accept_ok


def test_rbac_permission_evaluator():
    authz = AuthorizationService()

    # Org Owner
    ctx_owner = SecurityContext(
        user_id="usr_1",
        email="owner@acme.com",
        status=UserStatus.ACTIVE,
        org_role=OrgRole.OWNER,
        permissions=authz.get_effective_permissions(OrgRole.OWNER),
    )
    assert authz.evaluate_permission(ctx_owner, Permission.USER_SUSPEND)
    assert authz.evaluate_permission(ctx_owner, Permission.ORG_DELETE)

    # Member
    ctx_member = SecurityContext(
        user_id="usr_2",
        email="member@acme.com",
        status=UserStatus.ACTIVE,
        org_role=OrgRole.MEMBER,
        permissions=authz.get_effective_permissions(OrgRole.MEMBER),
    )
    assert not authz.evaluate_permission(ctx_member, Permission.USER_SUSPEND)
    assert authz.evaluate_permission(ctx_member, Permission.WORKSPACE_READ)

    # Suspended User (All permissions fail)
    ctx_suspended = SecurityContext(
        user_id="usr_3",
        email="suspended@acme.com",
        status=UserStatus.SUSPENDED,
        org_role=OrgRole.OWNER,
        permissions=authz.get_effective_permissions(OrgRole.OWNER),
    )
    assert not authz.evaluate_permission(ctx_suspended, Permission.ORG_READ)
