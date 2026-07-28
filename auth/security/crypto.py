"""
RAGTUNE Enterprise Identity & Access Management - Cryptographic Utilities
Password hashing (PBKDF2-HMAC-SHA256 600,000 rounds), token generation, SHA256 digest hashing.
"""

import hashlib
import hmac
import os
import secrets
from typing import Tuple

# OWASP Recommended Iterations for PBKDF2-HMAC-SHA256
HASH_ALGORITHM = "sha256"
HASH_ITERATIONS = 600000
SALT_SIZE_BYTES = 16


class CryptoService:
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashes password using PBKDF2-HMAC-SHA256 with 600,000 iterations.
        Format: pbkdf2_sha256$iterations$salt_hex$hash_hex
        """
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")

        salt = os.urandom(SALT_SIZE_BYTES)
        derived_key = hashlib.pbkdf2_hmac(
            HASH_ALGORITHM,
            password.encode("utf-8"),
            salt,
            HASH_ITERATIONS
        )
        return f"pbkdf2_sha256${HASH_ITERATIONS}${salt.hex()}${derived_key.hex()}"

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verifies plaintext password against PBKDF2 hash using constant-time comparison.
        """
        if not password or not hashed_password:
            return False

        try:
            parts = hashed_password.split("$")
            if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
                return False

            iterations = int(parts[1])
            salt = bytes.fromhex(parts[2])
            expected_key = bytes.fromhex(parts[3])

            derived_key = hashlib.pbkdf2_hmac(
                HASH_ALGORITHM,
                password.encode("utf-8"),
                salt,
                iterations
            )
            return hmac.compare_digest(derived_key, expected_key)
        except Exception:
            return False

    @staticmethod
    def generate_random_token(length_bytes: int = 32) -> str:
        """Generates cryptographically secure URL-safe random token string."""
        return secrets.token_urlsafe(length_bytes)

    @staticmethod
    def hash_token(token: str) -> str:
        """Computes SHA-256 digest of token string for safe database storage."""
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
