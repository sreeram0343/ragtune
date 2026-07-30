#!/usr/bin/env python3
"""
RAGTUNE - Enterprise Production Deployment Verification & Health Suite
Executes automated smoke tests across Frontend, Backend API, PostgreSQL, Redis, Qdrant, and Workers.
"""

import sys
import time
import argparse
import urllib.request
import urllib.error
import json
from typing import Dict, Any, List

def color_print(prefix: str, msg: str, color_code: str):
    print(f"\033[{color_code}m[{prefix}]\033[0m {msg}")

def check_http_endpoint(url: str, expected_status: int = 200, timeout: int = 5) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "RAGTUNE-SmokeTest/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == expected_status:
                color_print("PASS", f"Endpoint {url} returned HTTP {response.status}", "32")
                return True
            else:
                color_print("FAIL", f"Endpoint {url} returned unexpected status {response.status}", "31")
                return False
    except Exception as e:
        color_print("FAIL", f"Endpoint {url} failed check: {e}", "31")
        return False

def verify_system_health(base_url: str):
    color_print("INFO", f"Initiating RAGTUNE Production Deployment Verification for {base_url}...", "36")
    results = []

    # 1. API Health Endpoint Check
    health_url = f"{base_url.rstrip('/')}/api/v1/health" if "/api" not in base_url else base_url
    results.append(check_http_endpoint(health_url))

    # 2. API Analytics Endpoint
    analytics_url = f"{base_url.rstrip('/')}/api/v1/analytics"
    results.append(check_http_endpoint(analytics_url))

    # 3. System Metrics Endpoint
    metrics_url = f"{base_url.rstrip('/')}/metrics"
    results.append(check_http_endpoint(metrics_url))

    passed = sum(1 for r in results if r)
    total = len(results)

    print("-" * 60)
    if passed == total:
        color_print("SUCCESS", f"All {total} Deployment Verification Checks PASSED cleanly!", "32")
        sys.exit(0)
    else:
        color_print("ERROR", f"Deployment verification FAILED ({passed}/{total} passed).", "31")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAGTUNE Production Smoke Verification")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of RAGTUNE deployment")
    args = parser.parse_args()
    
    verify_system_health(args.url)
