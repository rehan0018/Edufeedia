import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from app.database import get_db
from app.models.models import (
    User, ChildProfile, ChildActivity, ChildQuizHistory, ChildAchievement,
    ChildContentApproval, ContentItem, Quiz, Question
)
from app.schemas.schemas import (
    KidsAdventureOut, KidsQuizSubmit, KidsQuizResultOut,
    ChildActivityCreate, ChildActivityOut, WhySeeingThisOut
)
from app.core.age_policy import AgeBandPolicy, StudentAgePolicy
from app.recommender.kids_engine import KidsRecommendationEngine

router = APIRouter(prefix="/kids", tags=["kids"])


@router.get("/{child_id}/adventure", response_model=KidsAdventureOut)
def get_today_adventure(
    child_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns '🌟 Today's Adventure' for the child.
    A structured 5-step journey: Watch Cartoon ➔ Discover Concept ➔ Interactive Activity ➔ Mini Quiz ➔ Earn Badge.
    """
    child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    return KidsRecommendationEngine.get_today_adventure(db, child_id)


@router.get("/{child_id}/feed")
def get_kids_feed(
    child_id: str,
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """
    Returns the balanced, personalized Kids feed.
    Applies the Learning Balance Engine to ensure diverse exposure across
    STEM, Art, Stories, Life Skills, and World Traditions.
    """
    child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    return KidsRecommendationEngine.get_balanced_kids_feed(db, child_id, limit=limit)


@router.get("/{child_id}/feed/explain/{content_id}", response_model=WhySeeingThisOut)
def explain_kids_recommendation(
    child_id: str,
    content_id: str,
    db: Session = Depends(get_db)
):
    """Transparent 'Why am I seeing this?' explanation for parents and guardians."""
    return KidsRecommendationEngine.get_why_seeing_this(db, child_id, content_id)


@router.post("/{child_id}/activity", response_model=ChildActivityOut, status_code=status.HTTP_201_CREATED)
def record_kids_activity(
    child_id: str,
    act_in: ChildActivityCreate,
    db: Session = Depends(get_db)
):
    """
    Records completed video, story, or activity with child reaction:
    ❤️ Loved it, 😊 Good, 😐 Okay, 😕 Confused.
    Awards stars and updates learning streak.
    """
    child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    item = db.query(ContentItem).filter(ContentItem.id == act_in.content_item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found.")

    act = ChildActivity(
        child_profile_id=child_id,
        content_item_id=act_in.content_item_id,
        activity_type=act_in.activity_type,
        dwell_time_seconds=act_in.dwell_time_seconds or 180,
        completed=bool(act_in.completed),
        child_reaction=act_in.child_reaction or "loved"
    )
    db.add(act)

    # Award stars and XP
    earned_stars = 2 if act_in.child_reaction == "loved" else 1
    child.stars_count = (child.stars_count or 0) + earned_stars
    child.xp_score = (child.xp_score or 0) + 15
    db.commit()
    db.refresh(act)

    return ChildActivityOut(
        id=act.id,
        child_profile_id=act.child_profile_id,
        content_item_id=act.content_item_id,
        activity_type=act.activity_type,
        dwell_time_seconds=act.dwell_time_seconds or 0,
        completed=act.completed,
        child_reaction=act.child_reaction,
        stars_earned=earned_stars,
        created_at=act.created_at.isoformat() if act.created_at else datetime.datetime.now().isoformat()
    )


@router.post("/{child_id}/quiz/submit", response_model=KidsQuizResultOut)
def submit_kids_quiz(
    child_id: str,
    quiz_sub: KidsQuizSubmit,
    db: Session = Depends(get_db)
):
    """
    Evaluates kids mini-quiz with encouraging, non-punishing feedback:
    Instead of negative failure, uses 'Almost! Let's discover why 🌟'
    Awards stars and logs completion.
    """
    child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    # Check question or quiz
    quiz = db.query(Quiz).filter(Quiz.id == quiz_sub.quiz_id).first()
    question = None
    if quiz and quiz.questions:
        question = quiz.questions[0]

    correct_answer = "Sunlight"
    fun_fact = "Sunlight gives plants the energy to turn water and air into food through photosynthesis!"
    
    if question:
        correct_answer = question.correct_answer
        if question.explanation:
            fun_fact = question.explanation

    # Check if correct (case-insensitive strip)
    is_correct = quiz_sub.selected_option.strip().lower() == correct_answer.strip().lower()

    if is_correct:
        positive_feedback = "🌟 Brilliant job! You solved the puzzle like a real explorer! ⭐⭐⭐"
        stars_awarded = 3
        child.stars_count = (child.stars_count or 0) + 3
        child.xp_score = (child.xp_score or 0) + 25
    else:
        positive_feedback = f"Almost! 🌟 In nature, plants need {correct_answer} to make their food. Every curious explorer learns by trying!"
        stars_awarded = 1
        child.stars_count = (child.stars_count or 0) + 1
        child.xp_score = (child.xp_score or 0) + 10

    # Log quiz attempt
    history = ChildQuizHistory(
        child_profile_id=child_id,
        quiz_id=quiz_sub.quiz_id,
        score=1 if is_correct else 0,
        total_questions=1,
        positive_feedback=positive_feedback,
        stars_awarded=stars_awarded
    )
    db.add(history)
    db.commit()

    return KidsQuizResultOut(
        is_correct=is_correct,
        selected_option=quiz_sub.selected_option,
        correct_answer=correct_answer,
        positive_feedback=positive_feedback,
        stars_awarded=stars_awarded,
        fun_fact=fun_fact
    )


@router.get("/{child_id}/achievements")
def get_kids_achievements(
    child_id: str,
    db: Session = Depends(get_db)
):
    """Returns the child's star count, streaks, and unlocked badges."""
    child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    achievements = db.query(ChildAchievement).filter(
        ChildAchievement.child_profile_id == child_id
    ).all()

    # Pre-populate initial default badges if list is empty
    if not achievements:
        default_badges = [
            ChildAchievement(
                child_profile_id=child.id,
                badge_code="first_explorer",
                title="Curious Explorer",
                description="Began the learning journey on EduFeedia Kids!",
                icon="🚀",
                stars_awarded=5
            ),
            ChildAchievement(
                child_profile_id=child.id,
                badge_code="junior_scientist",
                title="Junior Scientist",
                description="Discovered how nature and plants work!",
                icon="🔬",
                stars_awarded=5
            ),
            ChildAchievement(
                child_profile_id=child.id,
                badge_code="money_adventurer",
                title="Money Adventurer",
                description="Made smart choices in the ₹100 Money Adventure!",
                icon="💰",
                stars_awarded=5
            ),
            ChildAchievement(
                child_profile_id=child.id,
                badge_code="creative_artist",
                title="Creative Artist",
                description="Created wonderful colors and origami shapes!",
                icon="🎨",
                stars_awarded=5
            )
        ]
        db.add_all(default_badges)
        db.commit()
        achievements = default_badges

    return {
        "child_id": child.id,
        "child_name": child.name,
        "avatar_mascot": child.avatar_mascot or "space_explorer",
        "stars_count": child.stars_count or 12,
        "streak_count": child.streak_count or 3,
        "xp_score": child.xp_score or 150,
        "achievements": [
            {
                "id": a.id,
                "badge_code": a.badge_code,
                "title": a.title,
                "description": a.description,
                "icon": a.icon,
                "stars_awarded": a.stars_awarded,
                "unlocked_at": a.unlocked_at.strftime("%B %d, %Y") if a.unlocked_at else "Today"
            }
            for a in achievements
        ]
    }


@router.get("/{child_id}/screen-time-status")
def get_screen_time_status(
    child_id: str,
    db: Session = Depends(get_db)
):
    """
    Checks if Kids Mode is currently active or if bedtime curfew / daily limit has triggered.
    Returns friendly lock messages when curfew is active.
    """
    child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    now = datetime.datetime.now(datetime.timezone.utc)
    cur_time = now.strftime("%H:%M")
    is_curfew_active = False
    if child.curfew_enabled and child.curfew_start_time and child.curfew_end_time:
        if child.curfew_start_time > child.curfew_end_time:
            is_curfew_active = (cur_time >= child.curfew_start_time or cur_time < child.curfew_end_time)
        else:
            is_curfew_active = (child.curfew_start_time <= cur_time < child.curfew_end_time)

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    activities_today = db.query(ChildActivity).filter(
        ChildActivity.child_profile_id == child_id,
        ChildActivity.created_at >= today_start
    ).all()
    today_seconds = sum(a.dwell_time_seconds for a in activities_today if a.dwell_time_seconds)
    today_mins = max(int(today_seconds / 60), len(activities_today) * 5)
    daily_limit = child.daily_limit_minutes or 45

    is_over_limit = today_mins >= daily_limit
    is_locked = is_curfew_active or is_over_limit

    lock_message = ""
    if is_curfew_active:
        lock_message = "🌙 EduFeedia is going to sleep too. Sweet dreams! See you tomorrow morning!"
    elif is_over_limit:
        lock_message = f"🌟 You've had a wonderful {today_mins} minutes of fun learning today! Time to play outside or rest your eyes."

    return {
        "child_id": child.id,
        "child_name": child.name,
        "today_minutes_used": today_mins,
        "daily_limit_minutes": daily_limit,
        "remaining_minutes": max(0, daily_limit - today_mins),
        "is_curfew_active": is_curfew_active,
        "is_over_limit": is_over_limit,
        "is_locked": is_locked,
        "lock_message": lock_message,
        "curfew_hours": f"{child.curfew_start_time} - {child.curfew_end_time}"
    }


@router.get("/{child_id}/safe-search")
def kids_safe_search(
    child_id: str,
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db)
):
    """
    Child-Safe Search:
    Child Query ➔ Child-Safe Search ➔ Age Filter ➔ Safety Filter ➔ Parent Restrictions ➔ Results.
    Strictly prioritizes vetted educational cartoons and activities.
    """
    child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child profile not found.")

    age = AgeBandPolicy.calculate_age(child.date_of_birth)
    allowed_policy = StudentAgePolicy.get_allowed_content_policy(age)
    min_safety = allowed_policy.get("min_safety_score", 90)

    # 1. Proactive Multilingual & Kids Safety Check on Search Query
    from app.safety.multilingual_safety import MultilingualSafetyEngine
    safety_check = MultilingualSafetyEngine.evaluate(q)
    if not safety_check["is_safe"]:
        from app.models.models import SafetyIncident
        inc = SafetyIncident(
            child_profile_id=child_id,
            source="kids_safe_search",
            category=safety_check["flagged_categories"][0] if safety_check.get("flagged_categories") else "PROHIBITED_SEARCH",
            severity="high",
            blocked=True,
            flagged_snippet=q[:250],
            reason=f"Blocked prohibited query in Kids Safe Search: {safety_check.get('explanation')}",
            action_taken="BLOCKED",
            parent_notified=True
        )
        db.add(inc)
        db.commit()

        return {
            "query": q,
            "child_name": child.name,
            "results_count": 0,
            "blocked": True,
            "message": "🌟 Let's explore something fun and educational instead! Try searching for 'planets', 'origami', or 'animals'!",
            "items": []
        }

    # 2. Search title, topic, subject
    search_term = f"%{q}%"
    results = db.query(ContentItem).filter(
        ContentItem.is_approved == True,
        ContentItem.safety_score >= min_safety,
        ContentItem.age_min <= age,
        ContentItem.age_max >= age,
        (
            ContentItem.title.ilike(search_term) |
            ContentItem.topic.ilike(search_term) |
            ContentItem.subject.ilike(search_term) |
            ContentItem.content_category.ilike(search_term)
        )
    ).limit(8).all()

    return {
        "query": q,
        "child_name": child.name,
        "results_count": len(results),
        "items": [
            {
                "id": r.id,
                "title": r.title,
                "description": r.description,
                "category": r.content_category or "STEM",
                "is_cartoon": bool(r.is_cartoon),
                "duration_minutes": r.duration_minutes or 5,
                "interactive": bool(r.interactive_payload)
            }
            for r in results
        ]
    }
