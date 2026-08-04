"""
RAGTUNE Enterprise Identity & Access Management - JWT Handler
Generates, signs, decodes, and validates JWT Access Tokens.
"""

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from config.settings import settings


class JWTHandler:
    def __init__(self, secret_key: str | None = None):
        self.secret_key = (secret_key or settings.SECRET_KEY).encode("utf-8")
        self.issuer = "ragtune-iam"
        self.audience = "ragtune-api"

    def _base64url_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    def _base64url_decode(self, data_str: str) -> bytes:
        padding = "=" * (4 - (len(data_str) % 4))
        return base64.urlsafe_b64decode((data_str + padding).encode("utf-8"))

    def create_access_token(
        self,
        user_id: str,
        email: str,
        session_id: str,
        org_id: str | None = None,
        org_role: str | None = None,
        workspace_id: str | None = None,
        workspace_role: str | None = None,
        expires_delta_seconds: int = 900,  # 15 minutes default
    ) -> str:
        """
        Creates a signed JWT Access Token with security claims.
        """
        header = {"alg": "HS256", "typ": "JWT"}
        now = int(time.time())
        payload = {
            "iss": self.issuer,
            "aud": self.audience,
            "sub": user_id,
            "email": email,
            "sid": session_id,
            "org_id": org_id,
            "org_role": org_role,
            "ws_id": workspace_id,
            "ws_role": workspace_role,
            "iat": now,
            "nbf": now,
            "exp": now + expires_delta_seconds,
        }

        encoded_header = self._base64url_encode(json.dumps(header).encode("utf-8"))
        encoded_payload = self._base64url_encode(json.dumps(payload).encode("utf-8"))
        signing_input = f"{encoded_header}.{encoded_payload}".encode()

        signature = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
        encoded_signature = self._base64url_encode(signature)

        return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

    def decode_access_token(
        self, token: str
    ) -> tuple[bool, dict[str, Any] | None, str]:
        """
        Decodes, verifies signature, and checks expiration of JWT Access Token.
        Returns: (is_valid: bool, claims: dict, error_message: str)
        """
        if not token or token.count(".") != 2:
            return False, None, "Invalid token format"

        try:
            parts = token.split(".")
            encoded_header, encoded_payload, encoded_signature = (
                parts[0],
                parts[1],
                parts[2],
            )

            signing_input = f"{encoded_header}.{encoded_payload}".encode()
            expected_sig = hmac.new(
                self.secret_key, signing_input, hashlib.sha256
            ).digest()
            actual_sig = self._base64url_decode(encoded_signature)

            if not hmac.compare_digest(expected_sig, actual_sig):
                return False, None, "Invalid token signature"

            payload_bytes = self._base64url_decode(encoded_payload)
            payload = json.loads(payload_bytes.decode("utf-8"))

            now = int(time.time())
            if payload.get("exp", 0) < now:
                return False, None, "Token has expired"

            if payload.get("nbf", 0) > now:
                return False, None, "Token not active yet"

            return True, payload, "Token is valid"
        except Exception as e:
            return False, None, f"Token decode error: {e!s}"
