"""
RAGTUNE Enterprise Identity & Access Management - Token & Session Service
Handles JWT Access Tokens, Refresh Token Rotation (RTR), session tracking, and revocation.
"""

import uuid
from datetime import timedelta

from auth.domain.models import SessionDomain, utc_now
from auth.security.crypto import CryptoService
from auth.security.jwt_handler import JWTHandler
from auth.storage.auth_db import AuthDatabaseRepository

REFRESH_TOKEN_TTL_DAYS = 7


class TokenService:
    def __init__(self, repo: AuthDatabaseRepository):
        self.repo = repo
        self.jwt_handler = JWTHandler()

    def create_session_and_tokens(
        self,
        user_id: str,
        email: str,
        org_id: str | None = None,
        org_role: str | None = None,
        workspace_id: str | None = None,
        workspace_role: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[str, str, SessionDomain]:
        """
        Creates a new session, generates access & refresh tokens, and persists hashed session in DB.
        Returns: (access_token: str, refresh_token: str, session: SessionDomain)
        """
        session_id = f"sess_{uuid.uuid4().hex[:12]}"
        refresh_token = CryptoService.generate_random_token(32)
        refresh_hash = CryptoService.hash_token(refresh_token)

        expires_at = utc_now() + timedelta(days=REFRESH_TOKEN_TTL_DAYS)

        sess = SessionDomain(
            session_id=session_id,
            user_id=user_id,
            refresh_token_hash=refresh_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            is_revoked=False,
            expires_at=expires_at,
        )

        self.repo.create_session(sess)

        access_token = self.jwt_handler.create_access_token(
            user_id=user_id,
            email=email,
            session_id=session_id,
            org_id=org_id,
            org_role=org_role,
            workspace_id=workspace_id,
            workspace_role=workspace_role,
        )

        return access_token, refresh_token, sess

    def rotate_refresh_token(
        self,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> tuple[bool, str | None, str | None, str]:
        """
        Enforces Refresh Token Rotation (RTR).
        Validates current token, revokes previous session, and issues a new token pair.
        Returns: (success: bool, new_access_token: str, new_refresh_token: str, message: str)
        """
        if not refresh_token:
            return False, None, None, "Missing refresh token"

        token_hash = CryptoService.hash_token(refresh_token)
        sess = self.repo.get_session_by_hash(token_hash)

        if not sess:
            return False, None, None, "Invalid or unrecognized refresh token"

        if sess.is_revoked:
            # Possible token reuse attack! Revoke all sessions for safety.
            self.repo.revoke_all_user_sessions(sess.user_id)
            return (
                False,
                None,
                None,
                "Security violation: Revoked refresh token reused. All sessions invalidated.",
            )

        if sess.expires_at < utc_now():
            self.repo.revoke_session(sess.session_id)
            return False, None, None, "Refresh token has expired. Please log in again."

        user = self.repo.get_user_by_id(sess.user_id)
        if not user or user.status.value != "ACTIVE":
            self.repo.revoke_all_user_sessions(sess.user_id)
            return False, None, None, "User account is suspended or inactive"

        # Revoke old session (RTR requirement)
        self.repo.revoke_session(sess.session_id)

        # Issue fresh token pair
        new_access_token, new_refresh_token, _ = self.create_session_and_tokens(
            user_id=user.user_id,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return True, new_access_token, new_refresh_token, "Token rotated successfully"

    def revoke_session(self, session_id: str):
        """Revokes a specific active session."""
        self.repo.revoke_session(session_id)

    def revoke_all_sessions(self, user_id: str):
        """Revokes all active sessions for a user across all devices."""
        self.repo.revoke_all_user_sessions(user_id)
