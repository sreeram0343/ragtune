"""
RAGTUNE Enterprise Identity & Access Management - Database Storage Layer
SQLAlchemy ORM schemas and database persistence repository.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    create_engine, Column, String, Boolean, Integer, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from config.settings import settings
from auth.domain.models import (
    UserDomain, OrganizationDomain, WorkspaceDomain, ProjectDomain,
    OrganizationMemberDomain, WorkspaceMemberDomain, SessionDomain,
    InvitationDomain, AuditEventDomain, UserStatus, OrgStatus, InvitationStatus
)
from auth.domain.permissions import OrgRole, WorkspaceRole

Base = declarative_base()


class UserORM(Base):
    __tablename__ = "auth_users"

    user_id = Column(String(64), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    is_email_verified = Column(Boolean, default=False)
    status = Column(String(32), default="ACTIVE")
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OrganizationORM(Base):
    __tablename__ = "auth_organizations"

    org_id = Column(String(64), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    domain = Column(String(255), nullable=True)
    status = Column(String(32), default="ACTIVE")
    tier = Column(String(64), default="ENTERPRISE")
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkspaceORM(Base):
    __tablename__ = "auth_workspaces"

    workspace_id = Column(String(64), primary_key=True)
    org_id = Column(String(64), ForeignKey("auth_organizations.org_id"), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ProjectORM(Base):
    __tablename__ = "auth_projects"

    project_id = Column(String(64), primary_key=True)
    workspace_id = Column(String(64), ForeignKey("auth_workspaces.workspace_id"), nullable=False)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class OrganizationMemberORM(Base):
    __tablename__ = "auth_org_members"

    org_id = Column(String(64), ForeignKey("auth_organizations.org_id"), primary_key=True)
    user_id = Column(String(64), ForeignKey("auth_users.user_id"), primary_key=True)
    role = Column(String(64), default="MEMBER")
    joined_at = Column(DateTime, default=datetime.utcnow)


class WorkspaceMemberORM(Base):
    __tablename__ = "auth_workspace_members"

    workspace_id = Column(String(64), ForeignKey("auth_workspaces.workspace_id"), primary_key=True)
    user_id = Column(String(64), ForeignKey("auth_users.user_id"), primary_key=True)
    role = Column(String(64), default="MEMBER")
    joined_at = Column(DateTime, default=datetime.utcnow)


class SessionORM(Base):
    __tablename__ = "auth_sessions"

    session_id = Column(String(64), primary_key=True)
    user_id = Column(String(64), ForeignKey("auth_users.user_id"), nullable=False, index=True)
    refresh_token_hash = Column(String(64), unique=True, nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_revoked = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active_at = Column(DateTime, default=datetime.utcnow)


class InvitationORM(Base):
    __tablename__ = "auth_invitations"

    invitation_id = Column(String(64), primary_key=True)
    email = Column(String(255), nullable=False, index=True)
    org_id = Column(String(64), ForeignKey("auth_organizations.org_id"), nullable=False)
    workspace_id = Column(String(64), nullable=True)
    role = Column(String(64), nullable=False)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    status = Column(String(32), default="PENDING")
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditEventORM(Base):
    __tablename__ = "auth_audit_events"

    event_id = Column(String(64), primary_key=True)
    tenant_id = Column(String(64), default="default")
    org_id = Column(String(64), nullable=True)
    workspace_id = Column(String(64), nullable=True)
    actor_id = Column(String(64), nullable=False, index=True)
    event_type = Column(String(128), nullable=False, index=True)
    resource_type = Column(String(128), nullable=False)
    resource_id = Column(String(64), nullable=True)
    status = Column(String(32), default="SUCCESS")
    ip_address = Column(String(64), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)


class AuthDatabaseRepository:
    def __init__(self, db_url: Optional[str] = None):
        url = db_url or settings.DATABASE_URL
        self.engine = create_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False} if "sqlite" in url else {}
        )
        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.SessionLocal()

    # Mappers Domain <-> ORM
    def _user_to_domain(self, u: UserORM) -> UserDomain:
        return UserDomain(
            user_id=u.user_id,
            email=u.email,
            password_hash=u.password_hash,
            full_name=u.full_name,
            is_email_verified=u.is_email_verified,
            status=UserStatus(u.status),
            failed_login_attempts=u.failed_login_attempts,
            locked_until=u.locked_until,
            created_at=u.created_at,
            updated_at=u.updated_at
        )

    def get_user_by_email(self, email: str) -> Optional[UserDomain]:
        with self.get_session() as db:
            u = db.query(UserORM).filter(UserORM.email == email.lower().strip()).first()
            return self._user_to_domain(u) if u else None

    def get_user_by_id(self, user_id: str) -> Optional[UserDomain]:
        with self.get_session() as db:
            u = db.query(UserORM).filter(UserORM.user_id == user_id).first()
            return self._user_to_domain(u) if u else None

    def create_user(self, user: UserDomain) -> UserDomain:
        with self.get_session() as db:
            u = UserORM(
                user_id=user.user_id,
                email=user.email.lower().strip(),
                password_hash=user.password_hash,
                full_name=user.full_name,
                is_email_verified=user.is_email_verified,
                status=user.status.value,
                failed_login_attempts=user.failed_login_attempts,
                locked_until=user.locked_until
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            return self._user_to_domain(u)

    def update_user(self, user: UserDomain):
        with self.get_session() as db:
            u = db.query(UserORM).filter(UserORM.user_id == user.user_id).first()
            if u:
                u.email = user.email.lower().strip()
                u.password_hash = user.password_hash
                u.full_name = user.full_name
                u.is_email_verified = user.is_email_verified
                u.status = user.status.value
                u.failed_login_attempts = user.failed_login_attempts
                u.locked_until = user.locked_until
                u.updated_at = datetime.utcnow()
                db.commit()

    # Session Management
    def create_session(self, sess: SessionDomain) -> SessionDomain:
        with self.get_session() as db:
            s = SessionORM(
                session_id=sess.session_id,
                user_id=sess.user_id,
                refresh_token_hash=sess.refresh_token_hash,
                ip_address=sess.ip_address,
                user_agent=sess.user_agent,
                is_revoked=sess.is_revoked,
                expires_at=sess.expires_at
            )
            db.add(s)
            db.commit()
            return sess

    def get_session_by_hash(self, token_hash: str) -> Optional[SessionDomain]:
        with self.get_session() as db:
            s = db.query(SessionORM).filter(SessionORM.refresh_token_hash == token_hash).first()
            if not s:
                return None
            return SessionDomain(
                session_id=s.session_id,
                user_id=s.user_id,
                refresh_token_hash=s.refresh_token_hash,
                ip_address=s.ip_address,
                user_agent=s.user_agent,
                is_revoked=s.is_revoked,
                expires_at=s.expires_at,
                created_at=s.created_at,
                last_active_at=s.last_active_at
            )

    def revoke_session(self, session_id: str):
        with self.get_session() as db:
            db.query(SessionORM).filter(SessionORM.session_id == session_id).update({"is_revoked": True})
            db.commit()

    def revoke_all_user_sessions(self, user_id: str):
        with self.get_session() as db:
            db.query(SessionORM).filter(SessionORM.user_id == user_id).update({"is_revoked": True})
            db.commit()
