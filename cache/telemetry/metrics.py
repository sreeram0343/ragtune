"""
RAGTUNE Intelligent Caching System - Telemetry & Cost Savings Tracker
Tracks cache hit/miss statistics, latency reductions, stampede blocks, and estimated LLM cost savings.
"""

import time
import threading
from typing import Dict, Any

ESTIMATED_COST_PER_LLM_CALL = 0.003  # $0.003 average savings per cached LLM response


class CacheTelemetryTracker:
    def __init__(self):
        self._lock = threading.RLock()
        self._exact_hits = 0
        self._semantic_hits = 0
        self._misses = 0
        self._stampede_blocks = 0
        self._total_latency_saved_ms = 0.0

    def record_exact_hit(self, latency_saved_ms: float = 250.0):
        with self._lock:
            self._exact_hits += 1
            self._total_latency_saved_ms += latency_saved_ms

    def record_semantic_hit(self, similarity_score: float, latency_saved_ms: float = 250.0):
        with self._lock:
            self._semantic_hits += 1
            self._total_latency_saved_ms += latency_saved_ms

    def record_miss(self):
        with self._lock:
            self._misses += 1

    def record_stampede_block(self):
        with self._lock:
            self._stampede_blocks += 1

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            total_hits = self._exact_hits + self._semantic_hits
            total_requests = total_hits + self._misses
            hit_ratio = (total_hits / total_requests) if total_requests > 0 else 0.0
            estimated_cost_savings = round(total_hits * ESTIMATED_COST_PER_LLM_CALL, 4)

            return {
                "exact_hits": self._exact_hits,
                "semantic_hits": self._semantic_hits,
                "total_hits": total_hits,
                "misses": self._misses,
                "total_requests": total_requests,
                "hit_ratio": round(hit_ratio, 4),
                "stampede_blocks": self._stampede_blocks,
                "total_latency_saved_sec": round(self._total_latency_saved_ms / 1000.0, 2),
                "estimated_cost_savings_usd": estimated_cost_savings
            }
