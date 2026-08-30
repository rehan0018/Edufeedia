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

        grade = profile.school_class.grade_level if profile.school_class else 10
        board = profile.board or "CBSE"
        interests = profile.interests or []

        # 1. Generate Student Profile Embedding & Behavioral Profile
        student_vec = embed_student(
            interests=interests,
            board=board,
            grade_level=grade
        )
        behavioral_profile = get_user_behavioral_profile(db, student_id)

        # 2. Multi-Source Candidate Generation
        candidate_pool: Dict[str, Dict[str, Any]] = {}

        # Source A: Spaced Repetition items due today
        today = datetime.date.today()
        due_schedule = db.query(SpacedRepetitionSchedule).filter(
            SpacedRepetitionSchedule.student_user_id == student_id,
            SpacedRepetitionSchedule.next_review_date <= today
        ).first()

        if due_schedule:
            review_item = db.query(ContentItem).filter(
                ContentItem.subject.ilike(f"%{due_schedule.subject}%"),
                ContentItem.topic.ilike(f"%{due_schedule.topic}%"),
                ContentItem.is_approved == True
            ).first()
            if review_item:
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

        # Source D: Diagnostic Weak Topics from TopicMastery
        from app.models.models import TopicMastery
        weak_masteries = db.query(TopicMastery).filter(
            TopicMastery.student_user_id == student_id,
            (TopicMastery.mastery_score < 70) | (TopicMastery.trend == "declining")
        ).order_by(TopicMastery.mastery_score.asc()).limit(3).all()

        for wm in weak_masteries:
            weak_items = db.query(ContentItem).filter(
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

        # Source E: Trending / High-Quality fallback padding
        if len(candidate_pool) < limit:
            padding = db.query(ContentItem).filter(
                ContentItem.is_approved == True,
                ContentItem.grade_level == grade,
                ~ContentItem.id.in_(list(candidate_pool.keys())) if candidate_pool else True
            ).limit(limit - len(candidate_pool)).all()
            if not padding and len(candidate_pool) == 0:
                padding = db.query(ContentItem).filter(
                    ContentItem.is_approved == True
                ).limit(limit).all()
            for p in padding:
                if p.id not in candidate_pool:
                    candidate_pool[p.id] = {
                        "item": p,
                        "source": "trending"
                    }

        total_evaluated = len(candidate_pool)

        # Determine student target age dynamically via centralized Age Policy
        target_age = StudentAgePolicy.get_student_age(profile)

        # 3. Layer 1 Safety Hard Gate Evaluation
        safe_candidates = []
        for cid, data in candidate_pool.items():
            item = data["item"]
            # Safety Gate: Hard exclusion for unsafe items
            is_safe = SafetyEngine.is_safe_for_students(
                title=item.title,
                description=item.description or "",
                tags=item.tags,
                target_age=target_age
            )
            if is_safe and (item.safety_score is None or item.safety_score >= 80):
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

            # Boost spaced repetition and weak topic remedy items so intervention is prioritized
            if source == "spaced_repetition":
                score_data["total_relevance_score"] += 0.20
                score_data["relevance_percentage"] = min(100, score_data["relevance_percentage"] + 20)
            elif source == "weak_topic_remedy":
                score_data["total_relevance_score"] += 0.25
                score_data["relevance_percentage"] = min(100, score_data["relevance_percentage"] + 25)

            # Generate pedagogical explainability reason & reason code
            if source == "spaced_repetition":
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
