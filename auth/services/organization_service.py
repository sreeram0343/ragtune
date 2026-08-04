"""
RAGTUNE Enterprise Identity & Access Management - Multi-Tenant Organization Service
Manages Organizations, Workspaces, Projects, Memberships, and Invitation lifecycles.
"""

import re
import uuid
from datetime import timedelta

from auth.domain.models import (
    InvitationStatus,
    OrganizationDomain,
    OrgStatus,
    WorkspaceDomain,
    utc_now,
)
from auth.domain.permissions import OrgRole, WorkspaceRole
from auth.security.crypto import CryptoService
from auth.services.audit_service import AuditService
from auth.storage.auth_db import (
    AuthDatabaseRepository,
    InvitationORM,
    OrganizationMemberORM,
    OrganizationORM,
    WorkspaceMemberORM,
    WorkspaceORM,
)

INVITATION_TTL_DAYS = 7


class OrganizationService:
    def __init__(self, repo: AuthDatabaseRepository, audit_service: AuditService):
        self.repo = repo
        self.audit = audit_service

    def _slugify(self, text: str) -> str:
        s = re.sub(r"[^\w\s-]", "", text.lower()).strip()
        return re.sub(r"[-\s]+", "-", s)

    def create_organization(
        self, creator_user_id: str, name: str, domain: str | None = None
    ) -> tuple[bool, OrganizationDomain | None, WorkspaceDomain | None, str]:
        """
        Creates an Organization, assigns creator as OWNER, and creates default 'Main' workspace.
        """
        if not name or not name.strip():
            return False, None, None, "Organization name cannot be empty"

        org_id = f"org_{uuid.uuid4().hex[:12]}"
        slug = f"{self._slugify(name)}-{uuid.uuid4().hex[:4]}"

        org = OrganizationDomain(
            org_id=org_id,
            name=name.strip(),
            slug=slug,
            domain=domain.lower().strip() if domain else None,
            status=OrgStatus.ACTIVE,
        )

        workspace_id = f"ws_{uuid.uuid4().hex[:12]}"
        ws_slug = f"main-{uuid.uuid4().hex[:4]}"
        ws = WorkspaceDomain(
            workspace_id=workspace_id,
            org_id=org_id,
            name="Main Workspace",
            slug=ws_slug,
        )

        with self.repo.get_session() as db:
            org_orm = OrganizationORM(
                org_id=org.org_id,
                name=org.name,
                slug=org.slug,
                domain=org.domain,
                status=org.status.value,
                tier=org.tier,
            )
            db.add(org_orm)

            # Assign Owner member
            mem_orm = OrganizationMemberORM(
                org_id=org_id, user_id=creator_user_id, role=OrgRole.OWNER.value
            )
            db.add(mem_orm)

            # Add default Workspace
            ws_orm = WorkspaceORM(
                workspace_id=ws.workspace_id,
                org_id=ws.org_id,
                name=ws.name,
                slug=ws.slug,
            )
            db.add(ws_orm)

            # Assign Workspace Admin member
            ws_mem_orm = WorkspaceMemberORM(
                workspace_id=workspace_id,
                user_id=creator_user_id,
                role=WorkspaceRole.WORKSPACE_ADMIN.value,
            )
            db.add(ws_mem_orm)

            db.commit()

        self.audit.log_event(
            actor_id=creator_user_id,
            event_type="ORG_CREATE",
            resource_type="ORGANIZATION",
            resource_id=org_id,
            org_id=org_id,
            metadata={"name": name},
        )

        return True, org, ws, "Organization created successfully"

    def create_workspace(
        self, creator_user_id: str, org_id: str, name: str
    ) -> tuple[bool, WorkspaceDomain | None, str]:
        """Creates a new Workspace within an Organization."""
        if not name or not name.strip():
            return False, None, "Workspace name cannot be empty"

        ws_id = f"ws_{uuid.uuid4().hex[:12]}"
        slug = f"{self._slugify(name)}-{uuid.uuid4().hex[:4]}"
        ws = WorkspaceDomain(
            workspace_id=ws_id, org_id=org_id, name=name.strip(), slug=slug
        )

        with self.repo.get_session() as db:
            ws_orm = WorkspaceORM(
                workspace_id=ws.workspace_id,
                org_id=ws.org_id,
                name=ws.name,
                slug=ws.slug,
            )
            db.add(ws_orm)

            ws_mem_orm = WorkspaceMemberORM(
                workspace_id=ws_id,
                user_id=creator_user_id,
                role=WorkspaceRole.WORKSPACE_ADMIN.value,
            )
            db.add(ws_mem_orm)
            db.commit()

        self.audit.log_event(
            actor_id=creator_user_id,
            event_type="WORKSPACE_CREATE",
            resource_type="WORKSPACE",
            resource_id=ws_id,
            org_id=org_id,
            workspace_id=ws_id,
        )

        return True, ws, "Workspace created successfully"

    def create_invitation(
        self,
        sender_user_id: str,
        org_id: str,
        target_email: str,
        role: str = "MEMBER",
        workspace_id: str | None = None,
    ) -> tuple[bool, str | None, str]:
        """
        Creates a secure token invitation to join an Organization/Workspace.
        Returns: (success: bool, raw_token: str, message: str)
        """
        target_clean = target_email.lower().strip()
        raw_token = CryptoService.generate_random_token(32)
        token_hash = CryptoService.hash_token(raw_token)

        inv_id = f"inv_{uuid.uuid4().hex[:12]}"
        expires_at = utc_now() + timedelta(days=INVITATION_TTL_DAYS)

        with self.repo.get_session() as db:
            inv_orm = InvitationORM(
                invitation_id=inv_id,
                email=target_clean,
                org_id=org_id,
                workspace_id=workspace_id,
                role=role,
                token_hash=token_hash,
                status=InvitationStatus.PENDING.value,
                expires_at=expires_at,
            )
            db.add(inv_orm)
            db.commit()

        self.audit.log_event(
            actor_id=sender_user_id,
            event_type="INVITATION_SENT",
            resource_type="INVITATION",
            resource_id=inv_id,
            org_id=org_id,
            metadata={"target_email": target_clean, "role": role},
        )

        return True, raw_token, f"Invitation created for '{target_clean}'"

    def accept_invitation(
        self, accepting_user_id: str, raw_token: str
    ) -> tuple[bool, str]:
        """Accepts invitation token and adds user to Organization and Workspace."""
        token_hash = CryptoService.hash_token(raw_token)

        inv_id = None
        inv_org_id = None

        with self.repo.get_session() as db:
            inv = (
                db.query(InvitationORM)
                .filter(InvitationORM.token_hash == token_hash)
                .first()
            )
            if not inv or inv.status != InvitationStatus.PENDING.value:
                return False, "Invalid or expired invitation token"

            if inv.expires_at < utc_now():
                inv.status = InvitationStatus.EXPIRED.value
                db.commit()
                return False, "Invitation token has expired"

            inv_id = inv.invitation_id
            inv_org_id = inv.org_id

            # Add to Organization Membership if not already member
            existing_org_mem = (
                db.query(OrganizationMemberORM)
                .filter(
                    OrganizationMemberORM.org_id == inv.org_id,
                    OrganizationMemberORM.user_id == accepting_user_id,
                )
                .first()
            )

            if not existing_org_mem:
                db.add(
                    OrganizationMemberORM(
                        org_id=inv.org_id,
                        user_id=accepting_user_id,
                        role=(
                            inv.role
                            if inv.role in OrgRole.__members__
                            else OrgRole.MEMBER.value
                        ),
                    )
                )

            # Add to Workspace Membership if workspace_id specified
            if inv.workspace_id:
                existing_ws_mem = (
                    db.query(WorkspaceMemberORM)
                    .filter(
                        WorkspaceMemberORM.workspace_id == inv.workspace_id,
                        WorkspaceMemberORM.user_id == accepting_user_id,
                    )
                    .first()
                )
                if not existing_ws_mem:
                    db.add(
                        WorkspaceMemberORM(
                            workspace_id=inv.workspace_id,
                            user_id=accepting_user_id,
                            role=WorkspaceRole.MEMBER.value,
                        )
                    )

            inv.status = InvitationStatus.ACCEPTED.value
            db.commit()

        self.audit.log_event(
            actor_id=accepting_user_id,
            event_type="INVITATION_ACCEPTED",
            resource_type="INVITATION",
            resource_id=inv_id,
            org_id=inv_org_id,
        )

        return True, "Invitation accepted successfully"
