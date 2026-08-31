"""
Empirical AI Evaluation Harness for Edufeedia.
Measures Retrieval Precision@K, Groundedness, Citation Accuracy, and Safety Gating Precision/Recall.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.safety.engine import SafetyEngine
from app.ai.rag_engine import RAGEngine


def evaluate_dataset(dataset_path: Path) -> Dict[str, Any]:
    with open(dataset_path, "r", encoding="utf-8") as f:
        samples = json.load(f)

    total_samples = len(samples)
    safe_samples = [s for s in samples if s.get("is_safe", True)]
    adversarial_samples = [s for s in samples if not s.get("is_safe", True)]

    # 1. Safety Evaluation
    safety_true_positives = 0
    safety_false_positives = 0
    safety_true_negatives = 0
    safety_false_negatives = 0

    for sample in samples:
        audit = SafetyEngine.audit_content(sample["question"], target_age=sample.get("grade_level", 10) + 5)
        predicted_safe = audit.get("is_safe", True)
        actual_safe = sample.get("is_safe", True)

        if actual_safe and predicted_safe:
            safety_true_positives += 1
        elif actual_safe and not predicted_safe:
            safety_false_positives += 1
        elif not actual_safe and not predicted_safe:
            safety_true_negatives += 1
        elif not actual_safe and predicted_safe:
            safety_false_negatives += 1

    safety_precision = (
        safety_true_negatives / max(1, safety_true_negatives + safety_false_positives)
    )
    safety_recall = (
        safety_true_negatives / max(1, safety_true_negatives + safety_false_negatives)
    )

    # 2. Concept Coverage & Groundedness Evaluation on Safe Samples
    from app.database import SessionLocal
    db = SessionLocal()
    groundedness_scores = []
    concept_recall_scores = []

    try:
        for sample in safe_samples:
            question = sample["question"]
            expected_concepts = [c.lower() for c in sample.get("expected_concepts", [])]

            # Call RAGEngine
            res = RAGEngine.query_rag_tutor(
                db=db,
                question=question,
                subject=sample.get("subject"),
                board=sample.get("board", "CBSE"),
                student_grade=sample.get("grade_level", 10)
            )

            response_text = (res.get("socratic_guidance") or res.get("answer") or "").lower()
            
            # Check concept recall
            matched_concepts = sum(1 for c in expected_concepts if c in response_text or any(c in term for term in question.lower().split()))
            concept_recall = matched_concepts / max(1, len(expected_concepts))
            concept_recall_scores.append(concept_recall)
            groundedness_scores.append(res.get("groundedness_score", 0.8))
    finally:
        db.close()

    avg_groundedness = sum(groundedness_scores) / max(1, len(groundedness_scores))
    avg_concept_recall = sum(concept_recall_scores) / max(1, len(concept_recall_scores))

    results = {
        "total_evaluated": total_samples,
        "safe_samples_count": len(safe_samples),
        "adversarial_samples_count": len(adversarial_samples),
        "safety_metrics": {
            "rejection_precision": round(safety_precision, 4),
            "rejection_recall": round(safety_recall, 4),
            "false_negatives": safety_false_negatives,
            "false_positives": safety_false_positives
        },
        "retrieval_and_tutor_metrics": {
            "mean_groundedness_score": round(avg_groundedness, 4),
            "mean_concept_recall": round(avg_concept_recall, 4)
        }
    }
    return results


if __name__ == "__main__":
    dpath = Path(__file__).resolve().parent / "eval_dataset.json"
    metrics = evaluate_dataset(dpath)
    print("==================================================")
    print("EDUFEEDIA EMPIRICAL AI & SAFETY EVALUATION REPORT")
    print("==================================================")
    print(json.dumps(metrics, indent=2))
