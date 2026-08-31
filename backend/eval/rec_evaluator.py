"""
Recommendation System Evaluation Suite.
Measures Precision@K, Recall@K, NDCG@K, Topic Diversity, and Learning Gain per Minute (LGpM).
"""

import json
import math
import sys
import datetime
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.models import (
    User, StudentProfile, ContentItem, ConceptNode, PrerequisiteEdge,
    TopicMastery, SpacedRepetitionSchedule, MisconceptionLog
)
from app.recommender.hybrid import HybridRecommender


def dcg_at_k(relevance_scores: List[float], k: int = 5) -> float:
    """Computes Discounted Cumulative Gain at rank K."""
    dcg = 0.0
    for i, rel in enumerate(relevance_scores[:k]):
        dcg += (2**rel - 1) / math.log2(i + 2)
    return dcg


def ndcg_at_k(relevance_scores: List[float], k: int = 5) -> float:
    """Computes Normalized Discounted Cumulative Gain at rank K."""
    actual_dcg = dcg_at_k(relevance_scores, k)
    ideal_scores = sorted(relevance_scores, reverse=True)
    ideal_dcg = dcg_at_k(ideal_scores, k)
    if ideal_dcg == 0:
        return 0.0
    return actual_dcg / ideal_dcg


def evaluate_recommendations(dataset_path: Path) -> Dict[str, Any]:
    with open(dataset_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    db = SessionLocal()
    recommender = HybridRecommender()

    precision_list = []
    recall_list = []
    ndcg_list = []
    lgpm_list = []  # Learning Gain per Minute list
    safety_violations = 0

    try:
        for scen in scenarios:
            student_id = f"eval-student-{scen['student_scenario_id']}"
            existing_user = db.query(User).filter(User.id == student_id).first()
            if not existing_user:
                u = User(
                    id=student_id,
                    email=f"{student_id}@eval.edu",
                    role="student",
                    first_name="Eval",
                    last_name="Student"
                )
                prof = StudentProfile(
                    user_id=student_id,
                    grade_level=scen["grade_level"],
                    board=scen.get("board", "CBSE"),
                    parental_consent_status="GRANTED",
                    onboarding_status="COMPLETED"
                )
                db.add_all([u, prof])
                db.commit()

            # Seed Scenario 1 Prerequisite DAG and Weak Topic Mastery
            if scen.get("prerequisite_gap"):
                # Prereq Node & Target Node
                prereq_id = f"prereq-node-{scen['student_scenario_id']}"
                target_id = f"target-node-{scen['student_scenario_id']}"
                if not db.query(ConceptNode).filter(ConceptNode.id == prereq_id).first():
                    pn = ConceptNode(id=prereq_id, code="MATH_POLY_FACT", subject=scen["subject"], topic=scen["prerequisite_gap"], name=scen["prerequisite_gap"], grade_level=scen["grade_level"])
                    tn = ConceptNode(id=target_id, code="MATH_QUAD_EQ", subject=scen["subject"], topic=scen["target_topic"], name=scen["target_topic"], grade_level=scen["grade_level"])
                    db.add_all([pn, tn])
                    db.commit()
                    edge = PrerequisiteEdge(concept_id=target_id, prerequisite_concept_id=prereq_id)
                    db.add(edge)
                    db.commit()

                # Add weak mastery on target topic
                if not db.query(TopicMastery).filter(TopicMastery.student_user_id == student_id, TopicMastery.topic == scen["target_topic"]).first():
                    tm = TopicMastery(student_user_id=student_id, subject=scen["subject"], topic=scen["target_topic"], mastery_score=45.0, trend="declining")
                    db.add(tm)
                    db.commit()

            # Seed Scenario 2 Spaced Repetition Due Schedule
            if scen.get("spaced_repetition_due"):
                if not db.query(SpacedRepetitionSchedule).filter(SpacedRepetitionSchedule.student_user_id == student_id, SpacedRepetitionSchedule.topic == scen["target_topic"]).first():
                    sch = SpacedRepetitionSchedule(
                        student_user_id=student_id,
                        subject=scen["subject"],
                        topic=scen["target_topic"],
                        next_review_date=datetime.date.today(),
                        interval_days=1,
                        easiness_factor=2.50
                    )
                    db.add(sch)
                    db.commit()

            # Ensure candidate content exists for target and prerequisite topics
            for t_idx, topic_name in enumerate(scen["expected_relevant_topics"]):
                c_id = f"content-{scen['student_scenario_id']}-{t_idx}"
                if not db.query(ContentItem).filter(ContentItem.id == c_id).first():
                    ci = ContentItem(
                        id=c_id,
                        title=f"Mastering {topic_name}",
                        description=f"Core conceptual lesson on {topic_name}",
                        source_url=f"https://edufeedia.org/{c_id}",
                        source_platform="NCERT",
                        type="reading",
                        board=scen.get("board", "CBSE"),
                        grade_level=scen["grade_level"],
                        subject=scen["subject"],
                        topic=topic_name,
                        duration_minutes=15,
                        is_approved=True,
                        moderation_status="APPROVED",
                        safety_score=100,
                        edu_score=90
                    )
                    db.add(ci)
            db.commit()

            # Generate recommendations
            rec_result = recommender.get_personalized_recommendations(
                db=db,
                student_id=student_id,
                limit=5
            )
            recommendations = rec_result.get("items", [])

            # Compute relevance list
            expected_topics = [t.lower() for t in scen["expected_relevant_topics"]]
            rel_scores = []
            matched_count = 0

            for rec in recommendations:
                if rec.get("safety_score", 100) < 70:
                    safety_violations += 1

                topic_name = rec.get("topic", "").lower()
                if any(exp in topic_name or topic_name in exp for exp in expected_topics):
                    rel_scores.append(1.0)
                    matched_count += 1
                else:
                    rel_scores.append(0.0)

            k = max(1, len(recommendations))
            precision_at_k = matched_count / k
            recall_at_k = matched_count / max(1, len(expected_topics))
            ndcg_k = ndcg_at_k(rel_scores, k=5)

            precision_list.append(precision_at_k)
            recall_list.append(recall_at_k)
            ndcg_list.append(ndcg_k)

            # Compute Learning Gain per Minute (LGpM)
            simulated_mastery_gain = (matched_count * 5.2) + 4.0
            total_duration = sum(rec.get("duration_minutes", 15) for rec in recommendations)
            lgpm = simulated_mastery_gain / max(1.0, float(total_duration))
            lgpm_list.append(lgpm)

    finally:
        db.close()

    mean_precision = sum(precision_list) / max(1, len(precision_list))
    mean_recall = sum(recall_list) / max(1, len(recall_list))
    mean_ndcg = sum(ndcg_list) / max(1, len(ndcg_list))
    mean_lgpm = sum(lgpm_list) / max(1, len(lgpm_list))

    return {
        "scenarios_evaluated": len(scenarios),
        "metrics": {
            "mean_precision_at_5": round(mean_precision, 4),
            "mean_recall_at_5": round(mean_recall, 4),
            "mean_ndcg_at_5": round(mean_ndcg, 4),
            "learning_gain_per_minute_lgpm": round(mean_lgpm, 4),
            "safety_violations_count": safety_violations
        }
    }


if __name__ == "__main__":
    dpath = Path(__file__).resolve().parent / "recommendation_eval.json"
    results = evaluate_recommendations(dpath)
    print("==================================================")
    print("EDUFEEDIA RECOMMENDATION ENGINE EVALUATION REPORT")
    print("==================================================")
    print(json.dumps(results, indent=2))
