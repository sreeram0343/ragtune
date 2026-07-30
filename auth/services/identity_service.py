"""
RAGTUNE Enterprise Identity & Access Management - Identity Service
User registration, authentication, password management, activation, and suspension.
"""

import uuid
from datetime import datetime
from typing import Tuple, Optional, Dict, Any
from auth.security.crypto import CryptoService
from auth.security.rate_limiter import RateLimiterService
from auth.domain.models import UserDomain, UserStatus, utc_now
from auth.storage.auth_db import AuthDatabaseRepository
from auth.services.token_service import TokenService
from auth.services.audit_service import AuditService


class IdentityService:
    def __init__(
        self,
        repo: AuthDatabaseRepository,
        token_service: TokenService,
        audit_service: AuditService
    ):
        self.repo = repo
        self.token_service = token_service
        self.audit = audit_service
        self.rate_limiter = RateLimiterService()

    def register_user(
        self,
        email: str,
        password: str,
        full_name: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Optional[UserDomain], str]:
        """
        Registers a new user identity.
        """
        email_clean = email.lower().strip() if email else ""
        if not email_clean or "@" not in email_clean:
            return False, None, "Invalid email address format"

        if not password or len(password) < 8:
            return False, None, "Password must be at least 8 characters long"

        existing = self.repo.get_user_by_email(email_clean)
        if existing:
            return False, None, "User with this email already exists"

        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        pass_hash = CryptoService.hash_password(password)

        new_user = UserDomain(
            user_id=user_id,
            email=email_clean,
            password_hash=pass_hash,
            full_name=full_name.strip(),
            is_email_verified=False,
            status=UserStatus.ACTIVE
        )

        created = self.repo.create_user(new_user)
        self.audit.log_event(
            actor_id=user_id,
            event_type="USER_REGISTER",
            resource_type="USER",
            resource_id=user_id,
            ip_address=ip_address,
            metadata={"email": email_clean}
        )

        return True, created, "User registered successfully"

    def authenticate_user(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """
        Authenticates user credentials, enforces rate limiting & lockout rules, and issues tokens.
        """
        email_clean = email.lower().strip() if email else ""

        # Rate limiting velocity check
        if ip_address and self.rate_limiter.is_ip_rate_limited(ip_address):
            return False, None, "Too many login attempts from this IP. Please wait a minute."

        user = self.repo.get_user_by_email(email_clean)
        if not user:
            return False, None, "Invalid email or password"

        # Check Lockout status
        now = utc_now()
        if user.locked_until and user.locked_until > now:
            mins_left = int((user.locked_until - now).total_seconds() / 60) + 1
            return False, None, f"Account is temporarily locked due to multiple failed login attempts. Try again in {mins_left} minute(s)."

        # Check Account Status
        if user.status == UserStatus.SUSPENDED:
            return False, None, "Account has been suspended. Please contact enterprise administrator."

        # Verify Password
        if not CryptoService.verify_password(password, user.password_hash):
            # Increment failed attempts
            user.failed_login_attempts += 1
            should_lock, lockout_until = self.rate_limiter.calculate_lockout(user.failed_login_attempts)
            if should_lock:
                user.locked_until = datetime.fromtimestamp(lockout_until)
                self.audit.log_event(
                    actor_id=user.user_id,
                    event_type="USER_LOCKED",
                    resource_type="USER",
                    resource_id=user.user_id,
                    status="LOCKOUT",
                    ip_address=ip_address
                )

            self.repo.update_user(user)

            self.audit.log_event(
                actor_id=user.user_id,
                event_type="USER_LOGIN_FAILED",
                resource_type="USER",
                resource_id=user.user_id,
                status="FAILURE",
                ip_address=ip_address
            )

            return False, None, "Invalid email or password"

        # Successful Login -> Reset lockout counters
        user.failed_login_attempts = 0
        user.locked_until = None
        self.repo.update_user(user)

        # Issue Tokens & Session
        access_token, refresh_token, sess = self.token_service.create_session_and_tokens(
            user_id=user.user_id,
            email=user.email,
            ip_address=ip_address,
            user_agent=user_agent
        )

        self.audit.log_event(
            actor_id=user.user_id,
            event_type="USER_LOGIN_SUCCESS",
            resource_type="SESSION",
            resource_id=sess.session_id,
            ip_address=ip_address
        )

        return True, {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "Bearer",  # nosec B105
            "expires_in": 900,
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "full_name": user.full_name,
                "status": user.status.value
            }
        }, "Authentication successful"

    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, str]:
        """Changes user password and invalidates all existing sessions."""
        user = self.repo.get_user_by_id(user_id)
        if not user:
            return False, "User not found"

        if not CryptoService.verify_password(old_password, user.password_hash):
            return False, "Current password verification failed"

        if not new_password or len(new_password) < 8:
            return False, "New password must be at least 8 characters long"

        user.password_hash = CryptoService.hash_password(new_password)
        self.repo.update_user(user)

        # Security requirement: Invalidate all sessions upon password change
        self.token_service.revoke_all_sessions(user_id)

        self.audit.log_event(
            actor_id=user_id,
            event_type="PASSWORD_CHANGE",
            resource_type="USER",
            resource_id=user_id,
            ip_address=ip_address
        )

        return True, "Password updated successfully. All active sessions have been revoked."

    def suspend_user(self, admin_actor_id: str, target_user_id: str, ip_address: Optional[str] = None) -> Tuple[bool, str]:
        """Administratively suspends user and revokes all active sessions instantly."""
        user = self.repo.get_user_by_id(target_user_id)
        if not user:
            return False, "Target user not found"

        user.status = UserStatus.SUSPENDED
        self.repo.update_user(user)

        # Security requirement: Immediately revoke all active sessions
        self.token_service.revoke_all_sessions(target_user_id)

        self.audit.log_event(
            actor_id=admin_actor_id,
            event_type="USER_SUSPENDED",
            resource_type="USER",
            resource_id=target_user_id,
            ip_address=ip_address
        )

        return True, f"User '{target_user_id}' has been suspended and all sessions revoked."
