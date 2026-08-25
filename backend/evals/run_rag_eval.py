"""
Standalone RAG Evaluation Benchmark Runner.
Executes retrieval evaluation against backend/evals/rag/dataset.json
and computes quantitative MRR@3, Precision@3, and Recall@3 metrics.
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.ai.rag_engine import rag_engine

def run_rag_evaluation():
    dataset_path = BASE_DIR / "backend" / "evals" / "rag" / "dataset.json"
    if not dataset_path.exists():
        print(f"Dataset not found at {dataset_path}")
        return 1

    with open(dataset_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    print(f"Loaded {len(samples)} evaluation benchmark queries...")
    
    reciprocal_ranks = []
    precision_scores = []
    recall_scores = []

    for item in samples:
        query = item["question"]
        subject = item.get("subject", "Science")
        grade = item.get("grade_level", 10)
        expected_keywords = [kw.lower() for kw in item.get("expected_keywords", [])]

        expected_topic = item.get("expected_topic", "").lower()
        
        def normalize(t: str) -> str:
            return t.lower().replace("²", "^2").replace("√", "sqrt").replace("–", "-")

        results = rag_engine.retrieve_curriculum_context(
            query=query,
            grade=grade,
            subject=subject,
            top_k=3
        )

        def is_match(chunk: Dict[str, Any]) -> bool:
            c_text = normalize(chunk.get("text", ""))
            c_topic = chunk.get("topic", "").lower()
            if expected_topic and (expected_topic in c_topic or c_topic in expected_topic):
                return True
            return any(normalize(kw) in c_text for kw in expected_keywords)

        # Calculate Rank for MRR
        rank = 0
        for i, res in enumerate(results):
            if is_match(res):
                rank = i + 1
                break
        
        rr = (1.0 / rank) if rank > 0 else 0.0
        reciprocal_ranks.append(rr)

        # Precision@3 & Recall@3
        matching_chunks = sum(1 for res in results if is_match(res))
        prec = matching_chunks / max(1, len(results))
        precision_scores.append(prec)

        retrieved_combined = normalize(" ".join(r.get("text", "") for r in results))
        found_kws = sum(1 for kw in expected_keywords if normalize(kw) in retrieved_combined)
        rec = found_kws / max(1, len(expected_keywords))
        recall_scores.append(rec)

    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
    avg_precision = sum(precision_scores) / len(precision_scores) if precision_scores else 0.0
    avg_recall = sum(recall_scores) / len(recall_scores) if recall_scores else 0.0

    print("=" * 60)
    print("           RAG RETRIEVAL BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Evaluated Queries:    {len(samples)}")
    print(f"Mean Reciprocal Rank (MRR@3): {mrr:.2f}")
    print(f"Precision@3:                  {avg_precision:.2f}")
    print(f"Recall@3:                     {avg_recall:.2f}")
    print("=" * 60)

    assert mrr >= 0.80, f"MRR threshold failure: {mrr:.2f} < 0.80"
    print("SUCCESS: RAG evaluation benchmark passed!")
    return 0

if __name__ == "__main__":
    sys.exit(run_rag_evaluation())
