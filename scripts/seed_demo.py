#!/usr/bin/env python3
import argparse
import base64
import csv
import os
from typing import Dict, List, Tuple

import httpx

API_BASE_URL = "http://localhost:8001"
API_KEY = os.getenv("API_KEY", "test-key")

_client = httpx.Client(
    timeout=httpx.Timeout(120.0, connect=10.0),
    limits=httpx.Limits(max_keepalive_connections=10),
)

CHUNKING_STRATEGIES = ["fixed", "semantic", "late"]


def read_file(path: str) -> Tuple[str, str]:
    with open(path, "rb") as f:
        content = f.read()

    if path.endswith(".pdf"):
        mime = "application/pdf"
        content_b64 = base64.b64encode(content).decode("utf-8")
        return content_b64, mime
    elif path.endswith(".md"):
        mime = "text/markdown"
        return content.decode("utf-8"), mime
    else:
        mime = "text/plain"
        return content.decode("utf-8"), mime


def ingest_file(
    filepath: str, filename: str, chunking_strategy: str = "semantic", version: int = 1
) -> Dict:
    content, mime = read_file(filepath)

    payload = {
        "filename": filename,
        "content": content,
        "mime_type": mime,
        "version": version,
        "chunking_strategy": chunking_strategy,
    }

    response = _client.post(
        f"{API_BASE_URL}/ingest",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )
    response.raise_for_status()
    return response.json()


def run_query(query: str, top_k: int = 3, alpha: float = 0.5) -> Dict:
    payload = {
        "query": query,
        "top_k": top_k,
        "alpha": alpha,
    }

    response = _client.post(
        f"{API_BASE_URL}/query",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )
    response.raise_for_status()
    return response.json()


def run_evaluation(
    query: str, answer: str, contexts: list, reference: str = "", filename: str = ""
) -> Dict:
    payload = {
        "query": query,
        "answer": answer,
        "contexts": contexts,
    }
    if reference:
        payload["reference"] = reference
    if filename:
        payload["filename"] = filename

    response = _client.post(
        f"{API_BASE_URL}/evaluate",
        json=payload,
        headers={"X-API-Key": API_KEY},
    )
    response.raise_for_status()
    return response.json()


def print_query_result(label: str, query: str, result: Dict) -> None:
    print(f"\n--- {label} ---")
    print(f"Query: {query}")
    print(f"Answer: {result['answer'][:120]}...")
    print(f"Sources: {len(result['sources'])} chunk(s)")
    print(
        f"Tokens: {result.get('prompt_tokens', '?')} in / {result.get('completion_tokens', '?')} out"
    )
    print(f"Cost: ${result.get('estimated_cost_usd', 0):.6f}")
    print(f"Latency: {result.get('total_latency_ms', 0):.0f}ms")


def ingest_dataset_dir(dataset_dir: str) -> int:
    """Ingest all files from a generated dataset directory.

    Reads metadata.csv if available, assigns chunking strategies round-robin
    across documents, and ingests each file. Returns ingested count.
    """
    metadata: Dict[str, dict] = {}
    meta_path = os.path.join(dataset_dir, "metadata.csv")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                metadata[row["filename"]] = row

    files = sorted(
        f
        for f in os.listdir(dataset_dir)
        if f != "metadata.csv" and not f.startswith(".")
    )
    if not files:
        print(f"  No documents found in {dataset_dir}")
        return 0

    print(f"\n[1/3] Ingesting {len(files)} documents from {dataset_dir}...")
    ingested = 0
    for i, filename in enumerate(files):
        filepath = os.path.join(dataset_dir, filename)
        if not os.path.isfile(filepath):
            continue

        display_name = filename
        mime_type = "text/plain"
        if filename in metadata:
            display_name = metadata[filename].get("display_name", filename)
            mime_type = metadata[filename].get("mime_type", "text/plain")

        strategy = CHUNKING_STRATEGIES[i % len(CHUNKING_STRATEGIES)]

        with open(filepath, "r") as f:
            content = f.read()

        payload = {
            "filename": display_name,
            "content": content,
            "mime_type": mime_type,
            "version": 1,
            "chunking_strategy": strategy,
        }

        response = _client.post(
            f"{API_BASE_URL}/ingest",
            json=payload,
            headers={"X-API-Key": API_KEY},
        )
        response.raise_for_status()
        result = response.json()
        ingested += 1

        if ingested <= 3 or ingested % 50 == 0:
            print(
                f"  [{ingested}/{len(files)}] {display_name[:50]} -> "
                f"{result['chunk_count']} chunks, strategy={strategy}"
            )

    print(f"  Done: {ingested} documents ingested")
    return ingested


def run_queries_and_eval() -> dict:
    """Run the standard query suite and evaluation. Returns last query result."""
    queries: List[Tuple[str, str, int, float]] = [
        (
            "Alpha sweep: keyword-heavy",
            "What is the company policy on AI usage?",
            3,
            0.2,
        ),
        (
            "Alpha sweep: default hybrid",
            "What is the company policy on AI usage?",
            3,
            0.5,
        ),
        ("Alpha sweep: dense-heavy", "What is the company policy on AI usage?", 3, 0.8),
        ("Top-k comparison", "What is the company policy on AI usage?", 10, 0.5),
        ("Cross-document: technical", "How does the system architecture work?", 3, 0.5),
        ("Cross-document: FAQ", "What are the product supported languages?", 3, 0.5),
    ]

    print("\n[2/3] Running sample queries with varied parameters...")
    last_result = None
    for label, query, top_k, alpha in queries:
        result = run_query(query, top_k=top_k, alpha=alpha)
        print_query_result(label, query, result)
        last_result = result

    print("\n[3/3] Running evaluation on last query...")
    contexts = [s["text"] for s in last_result["sources"][:3]]
    reference = (
        "Employees must not use company AI tools for personal financial gain "
        "or to create content that violates company policies."
    )
    eval_result = run_evaluation(
        queries[-1][1],
        last_result["answer"],
        contexts,
        reference=reference,
        filename=last_result["sources"][0]["filename"],
    )

    print("\nEvaluation Scores:")
    print(f"  Faithfulness:    {eval_result['faithfulness']:.3f}")
    print(f"  Answer Relevancy: {eval_result['answer_relevancy']:.3f}")
    print(f"  Context Recall: {eval_result['context_recall']:.3f}")

    return last_result


def main():
    parser = argparse.ArgumentParser(
        description="Seed RAG platform with sample documents and run demo queries"
    )
    parser.add_argument(
        "--dataset-dir",
        type=str,
        default=None,
        help="Path to a generated dataset directory (from generate_synthetic_docs.py). "
        "When set, ingests all documents from this directory instead of samples/.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("RAG Production Starter - Demo Seed Script")
    print("=" * 60)

    if args.dataset_dir:
        count = ingest_dataset_dir(args.dataset_dir)
        if count == 0:
            print("No documents to ingest. Exiting.")
            return
    else:
        sample_dir = os.path.join(os.path.dirname(__file__), "samples")

        print("\n[1/3] Ingesting sample documents with varied strategies...")
        ingests = [
            ("company_policy.txt", "Company Policy", "fixed", 1),
            ("technical_overview.md", "Technical Overview", "semantic", 1),
            ("product_faq.txt", "Product FAQ", "late", 1),
        ]
        for filename, display_name, strategy, version in ingests:
            filepath = os.path.join(sample_dir, filename)
            if not os.path.exists(filepath):
                print(f"  Warning: {filepath} not found, skipping")
                continue
            result = ingest_file(
                filepath, display_name, chunking_strategy=strategy, version=version
            )
            print(
                f"  Ingested: {display_name} -> {result['chunk_count']} chunks, v{result['version']}, strategy={strategy}"
            )

        print("  Re-ingesting Company Policy with version bump + different strategy...")
        filepath = os.path.join(sample_dir, "company_policy.txt")
        result = ingest_file(
            filepath, "Company Policy", chunking_strategy="semantic", version=2
        )
        print(
            f"  Ingested: Company Policy -> {result['chunk_count']} chunks, v{result['version']}, strategy=semantic"
        )

    run_queries_and_eval()

    print("\n" + "=" * 60)
    print("Demo complete! 6 queries logged to MLflow rag-queries for comparison.")
    print("=" * 60)


if __name__ == "__main__":
    main()
