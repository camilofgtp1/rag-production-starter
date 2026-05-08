#!/usr/bin/env python3
"""
Concurrent load testing for the RAG query endpoint.

Usage:
    python scripts/load_test.py --concurrency 10 --requests 50
    python scripts/load_test.py --concurrency 20 --requests 200 --queries queries.txt
"""

import argparse
import concurrent.futures
import statistics
import time
from typing import List, Tuple

import httpx

API_BASE_URL = "http://localhost:8001"
API_KEY = "test-key"

DEFAULT_QUERIES: List[Tuple[str, int, float]] = [
    ("What is the company policy on AI usage?", 3, 0.5),
    ("How does the system architecture work?", 3, 0.5),
    ("What are the key features of the platform?", 3, 0.5),
    ("What support options are available?", 5, 0.3),
    ("How does data security work?", 10, 0.7),
    ("What is the pricing model?", 3, 0.5),
    ("How do I report a bug?", 3, 0.5),
    ("What platforms are supported?", 5, 0.5),
]


def run_single_query(
    client: httpx.Client, query: str, top_k: int, alpha: float
) -> dict:
    start = time.perf_counter()
    payload = {"query": query, "top_k": top_k, "alpha": alpha}
    response = client.post(
        f"{API_BASE_URL}/query",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )
    response.raise_for_status()
    elapsed = (time.perf_counter() - start) * 1000
    result = response.json()
    return {
        "latency_ms": elapsed,
        "status": response.status_code,
        "sources": len(result.get("sources", [])),
        "tokens_in": result.get("prompt_tokens", 0),
        "tokens_out": result.get("completion_tokens", 0),
        "cost": result.get("estimated_cost_usd", 0),
    }


def load_queries(path: str | None) -> list:
    if path is None:
        return DEFAULT_QUERIES
    queries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split("|")
                query = parts[0].strip()
                top_k = int(parts[1].strip()) if len(parts) > 1 else 3
                alpha = float(parts[2].strip()) if len(parts) > 2 else 0.5
                queries.append((query, top_k, alpha))
    return queries


def main():
    parser = argparse.ArgumentParser(description="Load test the RAG query endpoint")
    parser.add_argument(
        "--concurrency", type=int, default=5, help="Number of concurrent workers"
    )
    parser.add_argument(
        "--requests", type=int, default=20, help="Total number of requests"
    )
    parser.add_argument(
        "--queries",
        type=str,
        default=None,
        help="File with queries (one per line, format: query|top_k|alpha)",
    )
    args = parser.parse_args()

    queries = load_queries(args.queries)
    print("=" * 60)
    print(f"Load Test: {args.requests} requests x {args.concurrency} workers")
    print(f"Queries: {len(queries)} unique")
    print("=" * 60)

    results = []
    errors = 0
    start_time = time.perf_counter()

    with httpx.Client(
        timeout=httpx.Timeout(60.0, connect=10.0),
        limits=httpx.Limits(
            max_keepalive_connections=args.concurrency, max_connections=args.concurrency
        ),
    ) as client:

        def task(n: int) -> dict:
            query, top_k, alpha = queries[n % len(queries)]
            try:
                return run_single_query(client, query, top_k, alpha)
            except Exception as e:
                return {"latency_ms": 0, "status": 0, "error": str(e)}

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=args.concurrency
        ) as executor:
            futures = [executor.submit(task, i) for i in range(args.requests)]
            for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
                result = future.result()
                if result.get("error"):
                    errors += 1
                    print(f"  [{i}/{args.requests}] ERROR: {result['error'][:60]}")
                else:
                    results.append(result)
                    if i <= 3 or i % 10 == 0:
                        print(
                            f"  [{i}/{args.requests}] {result['latency_ms']:.0f}ms, {result['sources']} sources, ${result['cost']:.6f}"
                        )

    elapsed = time.perf_counter() - start_time
    latencies = [r["latency_ms"] for r in results]

    print()
    print("=" * 60)
    print("Results")
    print("=" * 60)
    print(f"  Total time:         {elapsed:.1f}s")
    print(f"  Successful:         {len(results)}")
    print(f"  Errors:             {errors}")
    print(f"  Throughput:         {args.requests / elapsed:.1f} req/s")
    if latencies:
        print(f"  Latency p50:        {statistics.median(latencies):.0f}ms")
        print(
            f"  Latency p95:        {sorted(latencies)[int(len(latencies) * 0.95)]:.0f}ms"
        )
        print(
            f"  Latency p99:        {sorted(latencies)[int(len(latencies) * 0.99)]:.0f}ms"
        )
        print(f"  Latency max:        {max(latencies):.0f}ms")
        avg_cost = sum(r["cost"] for r in results) / len(results)
        print(f"  Avg cost/query:     ${avg_cost:.6f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
