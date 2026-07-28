"""
RAGTUNE Enterprise Identity & Access Management - Identity Service Test Suite
"""

import pytest
from auth.storage.auth_db import AuthDatabaseRepository
from auth.services.audit_service import AuditService
from auth.services.token_service import TokenService
from auth.services.identity_service import IdentityService


def test_user_registration_and_authentication():
    repo = AuthDatabaseRepository("sqlite:///:memory:")
    audit = AuditService(repo)
    token_svc = TokenService(repo)
    identity_svc = IdentityService(repo, token_svc, audit)

    # 1. Register User
    success, user, msg = identity_svc.register_user(
        email="alice@enterprise.com",
        password="SecurePassword123!",
        full_name="Alice Enterprise"
    )
    assert success
    assert user is not None
    assert user.email == "alice@enterprise.com"

    # Duplicate registration prevention
    dup_success, _, _ = identity_svc.register_user(
        email="alice@enterprise.com",
        password="AnotherPassword123!",
        full_name="Alice Dup"
    )
    assert not dup_success

    # 2. Authenticate User
    auth_success, data, msg = identity_svc.authenticate_user(
        email="alice@enterprise.com",
        password="SecurePassword123!"
    )
    assert auth_success
    assert "access_token" in data
    assert "refresh_token" in data


def test_brute_force_lockout():
    repo = AuthDatabaseRepository("sqlite:///:memory:")
    audit = AuditService(repo)
    token_svc = TokenService(repo)
    identity_svc = IdentityService(repo, token_svc, audit)

    identity_svc.register_user("bob@enterprise.com", "CorrectPassword123!", "Bob Analyst")

    # Perform 5 consecutive failed logins
    for i in range(5):
        success, _, _ = identity_svc.authenticate_user("bob@enterprise.com", "WrongPassword!")
        assert not success

    # 6th attempt with correct password should be locked out
    locked_success, _, msg = identity_svc.authenticate_user("bob@enterprise.com", "CorrectPassword123!")
    assert not locked_success
    assert "locked" in msg.lower()


def test_password_change_and_session_invalidation():
    repo = AuthDatabaseRepository("sqlite:///:memory:")
    audit = AuditService(repo)
    token_svc = TokenService(repo)
    identity_svc = IdentityService(repo, token_svc, audit)

    identity_svc.register_user("charlie@enterprise.com", "OldPassword123!", "Charlie User")
    _, data, _ = identity_svc.authenticate_user("charlie@enterprise.com", "OldPassword123!")
    refresh_token = data["refresh_token"]

    # Change password
    change_ok, _ = identity_svc.change_password(
        user_id=data["user"]["user_id"],
        old_password="OldPassword123!",
        new_password="NewSecurePassword123!"
    )
    assert change_ok

    # Verify old session token rotation fails because session was revoked
    rotate_ok, _, _, msg = token_svc.rotate_refresh_token(refresh_token)
    assert not rotate_ok
