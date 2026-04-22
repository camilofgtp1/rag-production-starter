#!/usr/bin/env python3
import base64
import os
import sys
from typing import Dict, Tuple

import httpx

API_BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("API_KEY", "dev-key")


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


def ingest_file(filepath: str, filename: str) -> Dict:
    content, mime = read_file(filepath)
    
    payload = {
        "filename": filename,
        "content": content,
        "mime_type": mime,
        "version": 1,
    }
    
    response = httpx.post(
        f"{API_BASE_URL}/ingest",
        json=payload,
        headers={"X-API-Key": API_KEY},
        timeout=60.0,
    )
    response.raise_for_status()
    return response.json()


def run_query(query: str) -> Dict:
    payload = {
        "query": query,
        "top_k": 3,
        "alpha": 0.5,
    }
    
    response = httpx.post(
        f"{API_BASE_URL}/query",
        json=payload,
        headers={"X-API-Key": API_KEY},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def run_evaluation(query: str, answer: str, contexts: list) -> Dict:
    payload = {
        "query": query,
        "answer": answer,
        "contexts": contexts,
    }
    
    response = httpx.post(
        f"{API_BASE_URL}/evaluate",
        json=payload,
        headers={"X-API-Key": API_KEY},
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


def main():
    print("=" * 60)
    print("RAG Production Starter - Demo Seed Script")
    print("=" * 60)
    
    sample_dir = os.path.join(os.path.dirname(__file__), "samples")
    samples = [
        ("company_policy.txt", "Company Policy"),
        ("technical_overview.md", "Technical Overview"),
        ("product_faq.txt", "Product FAQ"),
    ]
    
    print("\n[1/3] Ingesting sample documents...")
    for filename, display_name in samples:
        filepath = os.path.join(sample_dir, filename)
        if not os.path.exists(filepath):
            print(f"  Warning: {filepath} not found, skipping")
            continue
        
        result = ingest_file(filepath, display_name)
        print(f"  Ingested: {display_name} -> {result['chunk_count']} chunks, version {result['version']}")
    
    print("\n[2/3] Running sample query...")
    query = "What is the company policy on AI usage?"
    result = run_query(query)
    
    print(f"\nQuery: {query}")
    print(f"\nAnswer: {result['answer']}")
    print("\nSources:")
    for source in result["sources"]:
        print(f"  - {source['filename']} (score: {source['score']:.3f})")
    
    print("\n[3/3] Running evaluation...")
    contexts = [s["text"] for s in result["sources"][:3]]
    eval_result = run_evaluation(query, result["answer"], contexts)
    
    print("\nEvaluation Scores:")
    print(f"  Faithfulness:    {eval_result['faithfulness']:.3f}")
    print(f"  Answer Relevancy: {eval_result['answer_relevancy']:.3f}")
    print(f"  Context Recall: {eval_result['context_recall']:.3f}")
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()