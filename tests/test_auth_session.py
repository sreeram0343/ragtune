"""
RAGTUNE Enterprise Identity & Access Management - Session & Token Test Suite
"""

from auth.services.audit_service import AuditService
from auth.services.identity_service import IdentityService
from auth.services.token_service import TokenService
from auth.storage.auth_db import AuthDatabaseRepository


def test_refresh_token_rotation_and_revocation():
    repo = AuthDatabaseRepository("sqlite:///:memory:")
    audit = AuditService(repo)
    token_svc = TokenService(repo)
    identity_svc = IdentityService(repo, token_svc, audit)

    identity_svc.register_user("diana@enterprise.com", "Password123!", "Diana Admin")
    _, data, _ = identity_svc.authenticate_user("diana@enterprise.com", "Password123!")

    access1 = data["access_token"]
    refresh1 = data["refresh_token"]

    # 1. First Refresh Call -> Successful Rotation
    ok1, access2, refresh2, _ = token_svc.rotate_refresh_token(refresh1)
    assert ok1
    assert access2 != access1
    assert refresh2 != refresh1

    # 2. Reuse Revoked Refresh Token (refresh1) -> Should trigger Security Violation & Revoke All Sessions
    ok_reuse, _, _, msg = token_svc.rotate_refresh_token(refresh1)
    assert not ok_reuse
    assert "security violation" in msg.lower()

    # 3. Subsequent attempt with refresh2 should now also fail because ALL user sessions were invalidated
    ok_new, _, _, _ = token_svc.rotate_refresh_token(refresh2)
    assert not ok_new
