"""
RAGTUNE Enterprise Identity & Access Management - Security Audit Logger Service
Immutably records security events, administrative actions, and access telemetry.
"""

import uuid
from typing import Any

from auth.domain.models import AuditEventDomain
from auth.storage.auth_db import AuditEventORM, AuthDatabaseRepository


class AuditService:
    def __init__(self, repo: AuthDatabaseRepository):
        self.repo = repo

    def log_event(
        self,
        actor_id: str,
        event_type: str,
        resource_type: str,
        resource_id: str | None = None,
        org_id: str | None = None,
        workspace_id: str | None = None,
        status: str = "SUCCESS",
        ip_address: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEventDomain:
        """
        Records an immutable audit event entry in storage.
        """
        evt = AuditEventDomain(
            event_id=f"evt_{uuid.uuid4().hex[:12]}",
            org_id=org_id,
            workspace_id=workspace_id,
            actor_id=actor_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            ip_address=ip_address,
            metadata=metadata or {},
        )

        with self.repo.get_session() as db:
            orm = AuditEventORM(
                event_id=evt.event_id,
                tenant_id=evt.tenant_id,
                org_id=evt.org_id,
                workspace_id=evt.workspace_id,
                actor_id=evt.actor_id,
                event_type=evt.event_type,
                resource_type=evt.resource_type,
                resource_id=evt.resource_id,
                status=evt.status,
                ip_address=evt.ip_address,
                metadata_json=evt.metadata,
                timestamp=evt.timestamp,
            )
            db.add(orm)
            db.commit()

        return evt

    def query_audit_logs(
        self,
        actor_id: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
    ) -> list[AuditEventDomain]:
        """Queries recorded audit logs."""
        with self.repo.get_session() as db:
            q = db.query(AuditEventORM)
            if actor_id:
                q = q.filter(AuditEventORM.actor_id == actor_id)
            if event_type:
                q = q.filter(AuditEventORM.event_type == event_type)

            results = q.order_by(AuditEventORM.timestamp.desc()).limit(limit).all()

            return [
                AuditEventDomain(
                    event_id=r.event_id,
                    tenant_id=r.tenant_id,
                    org_id=r.org_id,
                    workspace_id=r.workspace_id,
                    actor_id=r.actor_id,
                    event_type=r.event_type,
                    resource_type=r.resource_type,
                    resource_id=r.resource_id,
                    status=r.status,
                    ip_address=r.ip_address,
                    metadata=r.metadata_json or {},
                    timestamp=r.timestamp,
                )
                for r in results
            ]
