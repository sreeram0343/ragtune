"""
RAGTUNE Enterprise Identity & Access Management - Rate Limiter & Brute Force Defense
Tracks login failure velocity, exponential backoff, and account lockout thresholds.
"""

import time
from typing import Dict, Tuple, Optional

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 900  # 15 minutes


class RateLimiterService:
    def __init__(self):
        # In-memory IP velocity tracker: {ip_address: [timestamp1, timestamp2]}
        self._ip_attempts: Dict[str, list] = {}

    def is_ip_rate_limited(self, ip_address: str, max_requests: int = 30, window_seconds: int = 60) -> bool:
        """
        Verifies if IP address exceeds velocity limit within window_seconds.
        """
        if not ip_address:
            return False

        now = time.time()
        timestamps = self._ip_attempts.get(ip_address, [])
        # Clean older entries outside window
        timestamps = [t for t in timestamps if now - t < window_seconds]
        timestamps.append(now)
        self._ip_attempts[ip_address] = timestamps

        return len(timestamps) > max_requests

    def calculate_lockout(self, current_failed_count: int) -> Tuple[bool, Optional[float]]:
        """
        Determines if account should be locked based on failed attempt count.
        Returns: (should_lock: bool, lockout_until_timestamp: float)
        """
        new_count = current_failed_count + 1
        if new_count >= MAX_FAILED_ATTEMPTS:
            lockout_until = time.time() + LOCKOUT_DURATION_SECONDS
            return True, lockout_until
        return False, None
