"""
RAGTUNE Intelligent Caching System - Single-Flight Coalescing Engine
Prevents Cache Stampedes (Thundering Herd) by executing duplicate concurrent requests exactly once.
"""

import threading
from collections.abc import Callable
from typing import Any


class SingleFlightCall:
    def __init__(self):
        self.event = threading.Event()
        self.result: Any = None
        self.exception: Exception | None = None


class SingleFlightLock:
    """
    Coalesces concurrent identical function calls under the same key.
    Ensures expensive LLM/SQL computations execute once per cache miss.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._calls: dict[str, SingleFlightCall] = {}

    def execute(self, key: str, fn: Callable[[], Any]) -> Any:
        """
        Executes fn() for key. If a call for key is already in progress, waits
        for the leader call to complete and returns its shared result.
        """
        with self._lock:
            if key in self._calls:
                call = self._calls[key]
                is_leader = False
            else:
                call = SingleFlightCall()
                self._calls[key] = call
                is_leader = True

        if not is_leader:
            # Contender thread: wait for leader thread to complete
            call.event.wait()
            if call.exception:
                raise call.exception
            return call.result

        # Leader thread: execute calculation
        try:
            call.result = fn()
        except Exception as e:
            call.exception = e
        finally:
            with self._lock:
                self._calls.pop(key, None)
            call.event.set()

        if call.exception:
            raise call.exception
        return call.result
