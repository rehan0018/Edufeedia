import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.models.models import ContentItem, StudentProfile, SpacedRepetitionSchedule
from app.safety.engine import SafetyEngine
from app.embeddings.embedder import embed_student
from app.learning.feedback import get_user_behavioral_profile
from app.recommender.content_based import generate_content_based_candidates
from app.recommender.collaborative import generate_collaborative_candidates
from app.recommender.ranking import compute_hybrid_rank_score

from app.core.age_policy import StudentAgePolicy

class HybridRecommender:
    """
    End-to-End Multi-Stage Recommendation Engine with Hard Safety Gate.
    """

    @classmethod
    def get_personalized_recommendations(
        cls,
        db: Session,
        student_id: str,
        limit: int = 4
    ) -> Dict[str, Any]:
        profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
        if not profile:
            return {"items": [], "total_candidates_evaluated": 0}

        grade = profile.school_class.grade_level if profile.school_class else (profile.grade_level or 10)
        board = profile.board or "CBSE"
        interests = profile.interests or []

        # 1. Generate Student Profile Embedding & Behavioral Profile
        student_vec = embed_student(
            interests=interests,
            board=board,
            grade_level=grade
        )
        behavioral_profile = get_user_behavioral_profile(db, student_id)

        # 2. Multi-Source Candidate Generation strictly within Tenant Scope
        from app.core.tenant_scope import TenantScope
        candidate_pool: Dict[str, Dict[str, Any]] = {}

        # Source A: Spaced Repetition items due today (multi-item retrieval up to 15)
        today = datetime.date.today()
        due_schedules = db.query(SpacedRepetitionSchedule).filter(
            SpacedRepetitionSchedule.student_user_id == student_id,
            SpacedRepetitionSchedule.next_review_date <= today
        ).order_by(SpacedRepetitionSchedule.next_review_date.asc()).limit(15).all()

        for schedule in due_schedules:
            review_item = TenantScope.content(db, profile.user).filter(
                ContentItem.subject.ilike(f"%{schedule.subject}%"),
                ContentItem.topic.ilike(f"%{schedule.topic}%"),
                ContentItem.is_approved == True
            ).first()
            if review_item and review_item.id not in candidate_pool:
                candidate_pool[review_item.id] = {
                    "item": review_item,
                    "source": "spaced_repetition"
                }

        # Source B: Content-Based candidates
        cb_candidates = generate_content_based_candidates(db, profile, limit=12)
        for c in cb_candidates:
            cid = c["content_item"].id
            if cid not in candidate_pool:
                candidate_pool[cid] = {
                    "item": c["content_item"],
                    "source": "content_based"
                }

        # Source C: Collaborative candidates
        collab_candidates = generate_collaborative_candidates(db, profile, limit=8)
        for c in collab_candidates:
            cid = c["content_item"].id
            if cid not in candidate_pool:
                candidate_pool[cid] = {
                    "item": c["content_item"],
                    "source": "collaborative"
                }

        # Source D: Knowledge Graph Root Prerequisite Remediation
        from app.learning.knowledge_graph import KnowledgeGraphEngine
        from app.models.models import TopicMastery

        weak_masteries = db.query(TopicMastery).filter(
            TopicMastery.student_user_id == student_id,
            (TopicMastery.mastery_score < 75) | (TopicMastery.trend == "declining")
        ).order_by(TopicMastery.mastery_score.asc()).limit(3).all()

        for wm in weak_masteries:
            # Diagnose root prerequisite gaps via DAG traversal
            diag = KnowledgeGraphEngine.diagnose_learning_gaps(
                db=db,
                student_id=student_id,
                subject=wm.subject,
                topic=wm.topic
            )
            for prereq in diag.get("remediation_concepts", []):
                prereq_items = TenantScope.content(db, profile.user).filter(
                    ContentItem.subject.ilike(f"%{prereq['subject']}%"),
                    ContentItem.topic.ilike(f"%{prereq['topic']}%"),
                    ContentItem.is_approved == True
                ).limit(2).all()
                for pi in prereq_items:
                    if pi.id not in candidate_pool:
                        candidate_pool[pi.id] = {
                            "item": pi,
                            "source": "root_prerequisite_remedy",
                            "prereq_info": prereq,
                            "target_topic": wm.topic
                        }

            # Direct weak topic items
            weak_items = TenantScope.content(db, profile.user).filter(
                ContentItem.subject == wm.subject,
                ContentItem.topic.ilike(f"%{wm.topic}%"),
                ContentItem.is_approved == True
            ).limit(2).all()
            for wi in weak_items:
                if wi.id not in candidate_pool:
                    candidate_pool[wi.id] = {
                        "item": wi,
                        "source": "weak_topic_remedy"
                    }

        # Source E: Syllabus candidates strictly within tenant scope (no random cross-tenant padding)
        if len(candidate_pool) < limit:
            padding = TenantScope.content(db, profile.user).filter(
                ContentItem.is_approved == True,
                ContentItem.grade_level == grade,
                ~ContentItem.id.in_(list(candidate_pool.keys())) if candidate_pool else True
            ).limit(limit - len(candidate_pool)).all()
            for p in padding:
                if p.id not in candidate_pool:
                    candidate_pool[p.id] = {
                        "item": p,
                        "source": "trending"
                    }

        total_evaluated = len(candidate_pool)

        # Determine student target age dynamically via centralized Age Policy
        target_age = StudentAgePolicy.get_student_age(profile)
        allowed_policy = StudentAgePolicy.get_allowed_content_policy(target_age)
        min_safety = allowed_policy.get("min_safety_score", 80)

        # 3. Layer 1 Safety Hard Gate Evaluation — Strict Null and Score Verification
        safe_candidates = []
        for cid, data in candidate_pool.items():
            item = data["item"]
            
            # Reject candidates with missing safety scores or scores below threshold
            if item.safety_score is None or item.safety_score < min_safety:
                continue
            if item.edu_score is not None and item.edu_score < 0.35:
                continue

            # Textual and semantic content safety audit
            is_safe = SafetyEngine.is_safe_for_students(
                title=item.title,
                description=item.description or "",
                tags=item.tags,
                target_age=target_age
            )
            if is_safe:
                safe_candidates.append(data)

        # 4. Layer 4 Multi-Feature Hybrid Ranking
        ranked_results = []
        for cand in safe_candidates:
            item = cand["item"]
            source = cand["source"]

            score_data = compute_hybrid_rank_score(
                item=item,
                student_profile=profile,
                student_vector=student_vec,
                behavioral_profile=behavioral_profile,
                candidate_source=source
            )

            # Boost spaced repetition, weak topic, and root prerequisite remedy items so intervention is prioritized
            if source == "root_prerequisite_remedy":
                score_data["total_relevance_score"] += 0.35
                score_data["relevance_percentage"] = min(100, score_data["relevance_percentage"] + 35)
            elif source == "spaced_repetition":
                score_data["total_relevance_score"] += 0.20
                score_data["relevance_percentage"] = min(100, score_data["relevance_percentage"] + 20)
            elif source == "weak_topic_remedy":
                score_data["total_relevance_score"] += 0.25
                score_data["relevance_percentage"] = min(100, score_data["relevance_percentage"] + 25)

            # Generate pedagogical explainability reason & reason code
            if source == "root_prerequisite_remedy":
                prereq_name = cand.get("prereq_info", {}).get("concept_name", item.topic)
                target_top = cand.get("target_topic", item.subject)
                reason_code = "PREREQUISITE_DEFICIENCY_REMEDY"
                confidence = 0.95
                reason = f"Foundation review: Mastering prerequisite '{prereq_name}' is essential before advancing in {target_top}"
            elif source == "spaced_repetition":
                reason_code = "SPACED_REPETITION_DUE"
                confidence = 0.90
                reason = f"Due for active recall review in {item.topic} to solidify memory retention"
            elif source == "weak_topic_remedy":
                reason_code = "WEAK_TOPIC_REMEDY"
                confidence = 0.88
                reason = f"Targeted review to boost diagnostic mastery in {item.topic}"
            elif source == "interest_matching":
                reason_code = "INTEREST_MATCH"
                confidence = 0.80
                reason = f"Recommended based on your focus area in {item.subject}"
            elif source == "collaborative":
                reason_code = "PEER_MASTERY_TRENDING"
                confidence = 0.75
                reason = f"High mastery lesson among Grade {item.grade_level} peers"
            elif source == "semantic_search":
                reason_code = "CONCEPTUAL_PREREQUISITE"
                confidence = 0.82
                reason = f"Conceptually builds upon your recent study of {item.topic}"
            else:
                reason_code = "CURRICULUM_CORE"
                confidence = 0.78
                reason = f"Curriculum-essential lesson for Grade {item.grade_level} {item.subject}"

            ranked_results.append({
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "source_url": item.source_url,
                "source_platform": item.source_platform,
                "embed_code": item.embed_code,
                "type": item.type,
                "board": item.board,
                "grade_level": item.grade_level,
                "subject": item.subject,
                "topic": item.topic,
                "difficulty": item.difficulty,
                "duration_minutes": item.duration_minutes,
                "safety_score": item.safety_score or 100,
                "edu_score": item.edu_score or 95,
                "relevance_percentage": score_data["relevance_percentage"],
                "recommendation_reason": reason,
                "reason_code": reason_code,
                "confidence_score": confidence,
                "recommendation_source": source,
                "explanation": score_data
            })

        # Sort by total relevance score descending
        ranked_results.sort(key=lambda x: x["explanation"]["total_relevance_score"], reverse=True)

        return {
            "student_id": student_id,
            "greeting": f"Good morning, {profile.user.first_name}! 👋",
            "streak": profile.streak_count,
            "xp": profile.xp_score,
            "total_candidates_evaluated": total_evaluated,
            "items": ranked_results[:limit]
        }

recommender_instance = HybridRecommender()
