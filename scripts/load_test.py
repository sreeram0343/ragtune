#!/usr/bin/env python3
"""
RAGTUNE - Enterprise Load & Performance Benchmark Suite
Simulates concurrent user queries against FastAPI gateway and evaluates response latency, throughput, and error rates.
"""

import argparse
import concurrent.futures
import json
import statistics
import time
import urllib.parse
import urllib.request


def send_query_request(target_url: str, query: str) -> float:
    start_time = time.time()
    payload = json.dumps({"query": query}).encode("utf-8")
    req = urllib.request.Request(
        f"{target_url.rstrip('/')}/api/v1/query",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            _ = response.read()
            return time.time() - start_time
    except Exception:
        return -1.0


def run_load_test(target_url: str, total_requests: int, concurrency: int):
    print(f"Starting Load Test against {target_url}")
    print(f"Total Requests: {total_requests} | Concurrency: {concurrency}")

    sample_queries = [
        "What is the revenue growth for enterprise client ACME Corp?",
        "Summarize security compliance guidelines for financial data.",
        "What are the top active contracts in database?",
        "Explain RAGTUNE vector similarity threshold settings.",
    ]

    latencies = []
    failures = 0
    start_test_time = time.time()

    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(
                send_query_request, target_url, sample_queries[i % len(sample_queries)]
            )
            for i in range(total_requests)
        ]
        for future in concurrent.futures.as_completed(futures):
            latency = future.result()
            if latency > 0:
                latencies.append(latency * 1000.0)  # convert to ms
            else:
                failures += 1

    total_duration = time.time() - start_test_time
    rps = total_requests / total_duration if total_duration > 0 else 0

    print("\n" + "=" * 60)
    print(" LOAD TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f" Total Duration     : {total_duration:.2f} seconds")
    print(f" Successful Requests : {len(latencies)} / {total_requests}")
    print(f" Failed Requests     : {failures}")
    print(f" Throughput (RPS)    : {rps:.2f} req/sec")

    if latencies:
        print(f" Min Latency         : {min(latencies):.2f} ms")
        print(f" Max Latency         : {max(latencies):.2f} ms")
        print(f" Mean Latency        : {statistics.mean(latencies):.2f} ms")
        print(f" Median (p50)        : {statistics.median(latencies):.2f} ms")
        sorted_lat = sorted(latencies)
        p95_idx = int(len(sorted_lat) * 0.95)
        print(f" 95th Percentile p95 : {sorted_lat[p95_idx]:.2f} ms")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAGTUNE Load Testing Tool")
    parser.add_argument("--url", default="http://localhost:8000", help="Target API URL")
    parser.add_argument(
        "--requests", type=int, default=50, help="Total number of requests"
    )
    parser.add_argument(
        "--concurrency", type=int, default=10, help="Concurrent workers"
    )
    args = parser.parse_args()

    run_load_test(args.url, args.requests, args.concurrency)
