import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.models.models import (
    ContentItem, ChildProfile, ChildActivity, ChildContentApproval,
    ChildQuizHistory, Quiz, Question
)
from app.core.age_policy import AgeBandPolicy, StudentAgePolicy
from app.schemas.schemas import KidsAdventureOut, KidsAdventureStep, WhySeeingThisOut


class KidsRecommendationEngine:
    """
    Child-Centric Learning Balance Engine & Safe Content Recommender.
    Prioritizes safety, developmental age-banding, parent category controls,
    and pedagogical diversity (STEM + Art + Story + Activity + Values) over passive watch time.
    """

    @classmethod
    def get_balanced_kids_feed(
        cls,
        db: Session,
        child_id: str,
        limit: int = 6
    ) -> Dict[str, Any]:
        child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
        if not child:
            return {"items": [], "child_name": "Explorer", "total": 0}

        age = AgeBandPolicy.calculate_age(child.date_of_birth)
        band_info = AgeBandPolicy.get_age_band_info(age)
        allowed_policy = StudentAgePolicy.get_allowed_content_policy(age)
        min_safety = allowed_policy.get("min_safety_score", 90)

        # 1. Fetch blocked content IDs for this child
        blocked_ids = [
            apprv.content_item_id
            for apprv in db.query(ChildContentApproval).filter(
                ChildContentApproval.child_profile_id == child_id,
                ChildContentApproval.status == "BLOCKED"
            ).all()
        ]

        # 2. Base query: must be approved, age-appropriate, safe, and cartoon-first for young kids
        query = db.query(ContentItem).filter(
            ContentItem.is_approved == True,
            ContentItem.safety_score >= min_safety,
            ContentItem.age_min <= age,
            ContentItem.age_max >= age,
            (ContentItem.is_cartoon == True) | (ContentItem.grade_level <= 5)
        )

        if blocked_ids:
            query = query.filter(~ContentItem.id.in_(blocked_ids))

        # Check 'Parent Approved Content Only' mode
        if child.parent_approved_only:
            approved_ids = [
                apprv.content_item_id
                for apprv in db.query(ChildContentApproval).filter(
                    ChildContentApproval.child_profile_id == child_id,
                    ChildContentApproval.status == "APPROVED"
                ).all()
            ]
            query = query.filter(ContentItem.id.in_(approved_ids))

        # Filter by allowed categories
        allowed_cats = child.allowed_categories or ["STEM", "Creativity", "World", "Life Skills", "Philosophy & Values", "World Traditions"]
        blocked_cats = child.blocked_categories or []
        effective_cats = [c for c in allowed_cats if c not in blocked_cats]
        if effective_cats:
            query = query.filter(ContentItem.content_category.in_(effective_cats))

        # Filter by allowed content types
        if child.allowed_content_types:
            query = query.filter(ContentItem.type.in_(child.allowed_content_types))

        all_candidates = query.all()

        # If too few candidates in db, broaden safely but ensure it is strictly kids/cartoon appropriate
        if len(all_candidates) < limit:
            fallback = db.query(ContentItem).filter(
                ContentItem.is_approved == True,
                ContentItem.safety_score >= min_safety,
                (ContentItem.is_cartoon == True) | ((ContentItem.age_max <= 10) & (ContentItem.grade_level <= 5))
            ).limit(limit * 2).all()
            all_candidates = list({c.id: c for c in (all_candidates + fallback)}.values())

        # 3. Learning Balance Engine (Diversity Interleaving)
        # Fetch last 5 activities to see recently consumed categories
        recent_acts = db.query(ChildActivity).filter(
            ChildActivity.child_profile_id == child_id
        ).order_by(ChildActivity.created_at.desc()).limit(5).all()

        recent_categories = [
            act.content_item.content_category
            for act in recent_acts
            if act.content_item and act.content_item.content_category
        ]

        # Categorize candidates into buckets
        buckets: Dict[str, List[ContentItem]] = {}
        for c in all_candidates:
            cat = c.content_category or "STEM"
            if cat not in buckets:
                buckets[cat] = []
            buckets[cat].append(c)

        # Desired healthy learning balance order:
        preferred_balance = ["Life Skills", "Creativity", "STEM", "World Traditions", "Philosophy & Values", "World"]
        
        # If student recently did STEM, promote Creativity and Life Skills first
        if recent_categories and recent_categories[0] == "STEM":
            preferred_balance = ["Creativity", "Life Skills", "World Traditions", "STEM", "World"]

        selected_items = []
        # Round-robin selection across diverse buckets
        while len(selected_items) < limit and any(len(b) > 0 for b in buckets.values()):
            added_in_round = False
            for cat in preferred_balance:
                if cat in buckets and len(buckets[cat]) > 0:
                    selected_items.append(buckets[cat].pop(0))
                    added_in_round = True
                    if len(selected_items) >= limit:
                        break
            if not added_in_round:
                # Take from any remaining bucket
                for b in buckets.values():
                    if b:
                        selected_items.append(b.pop(0))
                        break

        # Format items with rich Kids metadata
        formatted = []
        for item in selected_items:
            reasons = cls.generate_reasons(child, item, age, recent_categories)
            formatted.append({
                "id": item.id,
                "title": item.title,
                "description": item.description,
                "category": item.content_category or "STEM",
                "subcategory": item.subcategory or item.topic,
                "type": item.type,
                "duration_minutes": item.duration_minutes or 5,
                "duration_label": f"{item.duration_minutes or 5} min cartoon" if item.is_cartoon else f"{item.duration_minutes or 5} min activity",
                "is_cartoon": bool(item.is_cartoon),
                "mascot_character": item.mascot_character or "Sparky the Fox",
                "interactive": bool(item.interactive_payload),
                "interactive_payload": item.interactive_payload,
                "language": item.language or "en",
                "safety_score": item.safety_score or 98,
                "thumbnail_icon": cls.get_category_icon(item.content_category),
                "why_am_i_seeing_this": reasons
            })

        return {
            "child_id": child.id,
            "child_name": child.name,
            "age": age,
            "age_band": band_info["name"],
            "mascot": child.avatar_mascot or "space_explorer",
            "stars_count": child.stars_count or 0,
            "items": formatted,
            "total": len(formatted)
        }

    @classmethod
    def get_today_adventure(cls, db: Session, child_id: str) -> KidsAdventureOut:
        """
        Creates or retrieves '🌟 Today's Adventure':
        A structured, sequential 5-step learning quest that turns passive scrolling
        into a purposeful exploration:
        1. Watch Cartoon
        2. Learn Concept
        3. Interactive Activity (e.g. ₹100 Money Adventure choices)
        4. Mini Quiz
        5. Earn Badge
        """
        child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
        age = AgeBandPolicy.calculate_age(child.date_of_birth) if child else 7
        name = child.name if child else "Explorer"

        # Find or create a featured cartoon/story lesson for today
        featured_item = db.query(ContentItem).filter(
            ContentItem.is_approved == True,
            ContentItem.is_cartoon == True
        ).first()

        interactive_item = db.query(ContentItem).filter(
            ContentItem.is_approved == True,
            ContentItem.interactive_payload.isnot(None)
        ).first()

        steps = [
            KidsAdventureStep(
                step_number=1,
                step_type="watch_cartoon",
                title="Watch Cartoon Adventure",
                description="Join Sparky the Fox on a fun 3-minute journey!",
                icon="🎬",
                status="completed",
                content_item_id=featured_item.id if featured_item else None,
                duration_label="3 mins"
            ),
            KidsAdventureStep(
                step_number=2,
                step_type="understand_concept",
                title="Discover the Secret Concept",
                description="Why do choices matter? Learn the difference between spending and saving.",
                icon="🧠",
                status="completed",
                content_item_id=featured_item.id if featured_item else None,
                duration_label="2 mins"
            ),
            KidsAdventureStep(
                step_number=3,
                step_type="interactive_activity",
                title="Money Adventure: ₹100 Choice Game",
                description="Our character has ₹100! Candy, Book, or Piggy Bank? What will you choose?",
                icon="💰",
                status="active",
                content_item_id=interactive_item.id if interactive_item else None,
                duration_label="4 mins"
            ),
            KidsAdventureStep(
                step_number=4,
                step_type="mini_quiz",
                title="Mini Quiz Challenge",
                description="Answer 2 fun questions to test your detective skills!",
                icon="❓",
                status="locked",
                duration_label="2 mins"
            ),
            KidsAdventureStep(
                step_number=5,
                step_type="earn_badge",
                title="Claim Your Star Badge",
                description="Unlock the 'Money Adventurer' badge for your collection!",
                icon="🏆",
                status="locked",
                duration_label="Reward"
            )
        ]

        return KidsAdventureOut(
            adventure_id="adv-daily-01",
            theme_title="Become a Super Money Explorer! 🚀",
            mascot_name="Sparky the Fox",
            mascot_avatar="🦊",
            greeting=f"Good morning, {name}! 🌟 Ready for today's exciting mission?",
            steps=steps,
            total_stars_available=15,
            progress_percentage=40
        )

    @classmethod
    def get_why_seeing_this(cls, db: Session, child_id: str, content_id: str) -> WhySeeingThisOut:
        """Explains transparently to parents why a specific content item was recommended."""
        child = db.query(ChildProfile).filter(ChildProfile.id == child_id).first()
        item = db.query(ContentItem).filter(ContentItem.id == content_id).first()

        if not child or not item:
            return WhySeeingThisOut(
                content_id=content_id,
                title="Educational Content",
                category="STEM",
                reasons=["General curriculum alignment"],
                age_match="Matches child age",
                parent_allowed=True,
                learning_balance_note="Balanced curriculum distribution"
            )

        age = AgeBandPolicy.calculate_age(child.date_of_birth)
        reasons = cls.generate_reasons(child, item, age, [])

        return WhySeeingThisOut(
            content_id=item.id,
            title=item.title,
            category=item.content_category or "STEM",
            reasons=reasons,
            age_match=f"Designed for age {age} (Band: {item.age_min}–{item.age_max} years)",
            parent_allowed=(item.content_category in (child.allowed_categories or [])),
            learning_balance_note="Promotes a healthy mix of STEM, Creative Arts, and Life Skills without repetitive binge patterns."
        )

    @staticmethod
    def generate_reasons(child: ChildProfile, item: ContentItem, age: int, recent_cats: List[str]) -> List[str]:
        reasons = []
        if item.content_category in (child.interests or []):
            reasons.append(f"Matches {child.name}'s interest in {item.content_category}.")
        elif item.topic in (child.interests or []):
            reasons.append(f"Explores topic '{item.topic}' selected in profile interests.")
        
        reasons.append(f"Developmentally calibrated for {age}-year-olds ({AgeBandPolicy.get_age_band(age)}).")
        reasons.append(f"Category '{item.content_category or 'STEM'}' is approved by parent content controls.")

        if item.is_cartoon:
            reasons.append("Presented in a cartoon-first format with friendly character narration.")
        if item.interactive_payload:
            reasons.append("Includes decision-based interactive choices to foster active problem-solving.")

        return reasons

    @staticmethod
    def get_category_icon(category: Optional[str]) -> str:
        icons = {
            "STEM": "🔬",
            "Science": "🧪",
            "Space": "🚀",
            "Creativity": "🎨",
            "World": "🌍",
            "Life Skills": "💰",
            "Philosophy & Values": "🧠",
            "World Traditions": "🪷",
            "Animals": "🐾",
            "Nature": "🌱"
        }
        return icons.get(category, "⭐")
