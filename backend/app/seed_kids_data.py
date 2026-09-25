import datetime
import uuid
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.database import SessionLocal, engine, Base
from app.models.models import (
    User, ChildProfile, ContentItem, Quiz, Question,
    ChildActivity, ChildAchievement, ChildQuizHistory
)
from app.core.security import get_password_hash

def seed_kids_ecosystem():
    db = SessionLocal()
    try:
        # 1. Ensure parent user exists
        parent = db.query(User).filter(User.email == "parent@gmail.com").first()
        if not parent:
            parent = User(
                email="parent@gmail.com",
                password_hash=get_password_hash("Parent123!"),
                role="parent",
                first_name="Rajesh",
                last_name="Kumar",
                is_verified=True,
                email_verified=True,
                identity_verified=True,
                account_status="ACTIVE",
                parent_pin_hash=get_password_hash("1234")
            )
            db.add(parent)
            db.commit()
            db.refresh(parent)
            print(f"Created parent user: {parent.email}")
        else:
            if not parent.parent_pin_hash:
                parent.parent_pin_hash = get_password_hash("1234")
                db.commit()
                print("Updated parent PIN hash.")

        # 2. Seed 3 Children (Aarav - 7, Sara - 5, Kabir - 9)
        today = datetime.date.today()
        dob_aarav = today.replace(year=today.year - 7)
        dob_sara = today.replace(year=today.year - 5)
        dob_kabir = today.replace(year=today.year - 9)

        children_data = [
            {
                "id": "c-aarav-07",
                "name": "Aarav",
                "dob": dob_aarav,
                "language": "en",
                "sec_lang": "hi",
                "learning_level": "intermediate",
                "avatar_mascot": "space_explorer",
                "interests": ["Science", "Space", "Art", "Money & Financial Literacy", "Robotics"],
                "stars": 18,
                "streak": 5,
                "xp": 320
            },
            {
                "id": "c-sara-05",
                "name": "Sara",
                "dob": dob_sara,
                "language": "en",
                "sec_lang": None,
                "learning_level": "beginner",
                "avatar_mascot": "dino",
                "interests": ["Animals", "Stories", "Nature", "Music", "Creativity"],
                "stars": 12,
                "streak": 3,
                "xp": 180
            },
            {
                "id": "c-kabir-09",
                "name": "Kabir",
                "dob": dob_kabir,
                "language": "en",
                "sec_lang": "mr",
                "learning_level": "advanced",
                "avatar_mascot": "robot",
                "interests": ["STEM", "Mathematics", "Robotics", "Puzzles & Logic", "Experiments"],
                "stars": 24,
                "streak": 7,
                "xp": 450
            }
        ]

        created_children = {}
        for c in children_data:
            existing = db.query(ChildProfile).filter(ChildProfile.id == c["id"]).first()
            if not existing:
                child = ChildProfile(
                    id=c["id"],
                    parent_user_id=parent.id,
                    name=c["name"],
                    date_of_birth=c["dob"],
                    preferred_language=c["language"],
                    secondary_language=c["sec_lang"],
                    learning_level=c["learning_level"],
                    avatar_mascot=c["avatar_mascot"],
                    interests=c["interests"],
                    allowed_categories=["STEM", "Creativity", "World", "Life Skills", "Philosophy & Values", "World Traditions"],
                    blocked_categories=[],
                    allowed_content_types=["video", "story", "activity", "quiz", "game"],
                    parent_approved_only=False,
                    daily_limit_minutes=45,
                    curfew_start_time="20:00",
                    curfew_end_time="07:00",
                    curfew_enabled=True,
                    xp_score=c["xp"],
                    streak_count=c["streak"],
                    stars_count=c["stars"]
                )
                db.add(child)
                created_children[c["name"]] = child
                print(f"Created child profile: {c['name']} (Age: {today.year - c['dob'].year})")
            else:
                created_children[c["name"]] = existing

        db.commit()

        # 3. Seed High-Quality Kids Cartoon & Interactive Lessons
        content_items = [
            {
                "id": "k-content-01",
                "title": "Money Adventure: The ₹100 Dilemma",
                "description": "Our friendly squirrel Sparky receives ₹100! Candy, Book, or Piggy Bank? Help Sparky choose and discover the magic of saving!",
                "source_url": "https://edufeedia.org/kids/money-adventure-100",
                "source_platform": "EduFeedia Originals",
                "type": "game",
                "board": "Universal",
                "grade_level": 2,
                "subject": "Life Skills",
                "topic": "Money Basics & Saving",
                "content_category": "Life Skills",
                "subcategory": "Financial Literacy",
                "difficulty": "easy",
                "duration_minutes": 4,
                "safety_score": 100,
                "edu_score": 98,
                "age_min": 5,
                "age_max": 10,
                "is_cartoon": True,
                "mascot_character": "Sparky the Squirrel",
                "is_approved": True,
                "interactive_payload": {
                    "scenario": "Sparky gets ₹100 for helping his grandmother clean the garden. What should he do?",
                    "starting_amount": 100,
                    "choices": [
                        {
                            "id": "candy",
                            "text": "🍭 Spend ₹40 on colourful candy",
                            "cost": 40,
                            "reaction": "Yum! Sweet treat! But soon it's all eaten up.",
                            "badge_earned": "Sweet Tooth"
                        },
                        {
                            "id": "book",
                            "text": "📚 Buy a fun picture book for ₹30",
                            "cost": 30,
                            "reaction": "Awesome! You can read this book again and again with friends.",
                            "badge_earned": "Book Explorer"
                        },
                        {
                            "id": "piggy_bank",
                            "text": "🐷 Put ₹50 into the golden piggy bank",
                            "cost": 50,
                            "reaction": "Clink! That ₹50 is safe for a rainy day or a future telescope!",
                            "badge_earned": "Master Saver"
                        }
                    ],
                    "lesson_takeaway": "Smart explorers divide their money: a little for fun, a little for learning, and a lot for the piggy bank!"
                }
            },
            {
                "id": "k-content-02",
                "title": "Sparky's Solar System Voyage",
                "description": "Hop aboard the star cruiser! Fly past the red planet Mars, zip around Jupiter's giant storm, and marvel at Saturn's icy rings.",
                "source_url": "https://edufeedia.org/kids/solar-system-voyage",
                "source_platform": "EduFeedia Originals",
                "type": "video",
                "board": "Universal",
                "grade_level": 2,
                "subject": "Science",
                "topic": "Space & Planets",
                "content_category": "STEM",
                "subcategory": "Space Science",
                "difficulty": "easy",
                "duration_minutes": 5,
                "safety_score": 100,
                "edu_score": 96,
                "age_min": 4,
                "age_max": 10,
                "is_cartoon": True,
                "mascot_character": "Cosmo Fox",
                "is_approved": True,
                "interactive_payload": {
                    "quiz_checkpoint": {
                        "question": "Which planet has giant icy rings around it?",
                        "options": ["Saturn", "Mars", "The Moon"],
                        "answer": "Saturn"
                    }
                }
            },
            {
                "id": "k-content-03",
                "title": "How Plants Drink: The Mystery of Sunlight & Water",
                "description": "Join Robo-Owl in the rooftop garden! Watch roots drink water like tiny straws and leaves capture sunlight to bake green food.",
                "source_url": "https://edufeedia.org/kids/how-plants-drink",
                "source_platform": "EduFeedia Originals",
                "type": "video",
                "board": "Universal",
                "grade_level": 3,
                "subject": "Science",
                "topic": "Plant Biology",
                "content_category": "STEM",
                "subcategory": "Biology",
                "difficulty": "easy",
                "duration_minutes": 4,
                "safety_score": 99,
                "edu_score": 95,
                "age_min": 5,
                "age_max": 10,
                "is_cartoon": True,
                "mascot_character": "Robo-Owl",
                "is_approved": True,
                "interactive_payload": None
            },
            {
                "id": "k-content-04",
                "title": "Dino's Colour Magic & Origami Studio",
                "description": "Mix blue and yellow to create fresh mint green! Fold a colourful paper puppy step-by-step with Dino.",
                "source_url": "https://edufeedia.org/kids/dino-origami-colors",
                "source_platform": "EduFeedia Originals",
                "type": "activity",
                "board": "Universal",
                "grade_level": 1,
                "subject": "Arts",
                "topic": "Color Theory & Craft",
                "content_category": "Creativity",
                "subcategory": "Art & Craft",
                "difficulty": "easy",
                "duration_minutes": 6,
                "safety_score": 100,
                "edu_score": 94,
                "age_min": 4,
                "age_max": 9,
                "is_cartoon": True,
                "mascot_character": "Dino Artist",
                "is_approved": True,
                "interactive_payload": {
                    "steps": [
                        "Take a square sheet of coloured craft paper.",
                        "Fold corner to corner to make a triangle.",
                        "Fold down the ears and draw tiny eyes and a nose!"
                    ]
                }
            },
            {
                "id": "k-content-05",
                "title": "The Lion and the Tiny Mouse: True Kindness",
                "description": "Even the smallest friend can help the mightiest king. A timeless Panchatantra story about empathy, courage, and keeping promises.",
                "source_url": "https://edufeedia.org/kids/lion-and-mouse",
                "source_platform": "EduFeedia Originals",
                "type": "story",
                "board": "Universal",
                "grade_level": 2,
                "subject": "Values",
                "topic": "Empathy & Kindness",
                "content_category": "Philosophy & Values",
                "subcategory": "Moral Tales",
                "difficulty": "easy",
                "duration_minutes": 5,
                "safety_score": 100,
                "edu_score": 97,
                "age_min": 4,
                "age_max": 10,
                "is_cartoon": True,
                "mascot_character": "Grandpa Banyan",
                "is_approved": True,
                "interactive_payload": None
            },
            {
                "id": "k-content-06",
                "title": "Stories of Light: Celebrations Across the World",
                "description": "From Diwali diyas and Hanukkah menorahs to lanterns of Mid-Autumn festivals: discovering how cultures celebrate hope and warmth.",
                "source_url": "https://edufeedia.org/kids/festivals-of-light",
                "source_platform": "EduFeedia Originals",
                "type": "story",
                "board": "Universal",
                "grade_level": 3,
                "subject": "World Traditions",
                "topic": "Cultural Traditions",
                "content_category": "World Traditions",
                "subcategory": "Cultural Stories",
                "difficulty": "easy",
                "duration_minutes": 5,
                "safety_score": 100,
                "edu_score": 95,
                "age_min": 6,
                "age_max": 10,
                "is_cartoon": True,
                "mascot_character": "Traveler Bird",
                "is_approved": True,
                "interactive_payload": None
            },
            {
                "id": "k-content-07",
                "title": "The Water Drop Detective: Save Every Drop",
                "description": "Where does tap water come from? Travel inside clouds and rivers with droplet Pippa, and learn 3 easy ways to stop leaky waste at home.",
                "source_url": "https://edufeedia.org/kids/water-drop-detective",
                "source_platform": "EduFeedia Originals",
                "type": "video",
                "board": "Universal",
                "grade_level": 2,
                "subject": "Environment",
                "topic": "Water Conservation",
                "content_category": "World",
                "subcategory": "Nature & Environment",
                "difficulty": "easy",
                "duration_minutes": 4,
                "safety_score": 100,
                "edu_score": 96,
                "age_min": 5,
                "age_max": 10,
                "is_cartoon": True,
                "mascot_character": "Pippa the Droplet",
                "is_approved": True,
                "interactive_payload": None
            }
        ]

        for item in content_items:
            existing = db.query(ContentItem).filter(ContentItem.id == item["id"]).first()
            if not existing:
                c_item = ContentItem(**item)
                db.add(c_item)
                print(f"Added Kids content: {item['title']}")

        db.commit()

        # 4. Seed Kids Mini-Quiz linked to Plant Biology
        quiz_plant = db.query(Quiz).filter(Quiz.id == "k-quiz-plant-01").first()
        if not quiz_plant:
            quiz_plant = Quiz(
                id="k-quiz-plant-01",
                content_item_id="k-content-03",
                title="Plant Detective Challenge"
            )
            db.add(quiz_plant)
            db.flush()

            q1 = Question(
                id="k-q-plant-01",
                quiz_id=quiz_plant.id,
                question_text="What do green leaves need from the sky to bake their food?",
                options=["Sunlight", "Chocolate", "Television"],
                correct_answer="Sunlight",
                explanation="Sunlight gives plants natural energy to make sweet glucose for their stems and flowers!",
                difficulty="easy"
            )
            db.add(q1)
            print("Added Kids mini-quiz: Plant Detective Challenge")

        db.commit()

        # 5. Seed initial activity logs for Aarav so Parent Dashboard shows rich live charts
        aarav_id = "c-aarav-07"
        acts = db.query(ChildActivity).filter(ChildActivity.child_profile_id == aarav_id).all()
        if not acts:
            seed_acts = [
                ChildActivity(
                    child_profile_id=aarav_id,
                    content_item_id="k-content-01",
                    activity_type="game",
                    dwell_time_seconds=240,
                    completed=True,
                    child_reaction="loved"
                ),
                ChildActivity(
                    child_profile_id=aarav_id,
                    content_item_id="k-content-02",
                    activity_type="video",
                    dwell_time_seconds=300,
                    completed=True,
                    child_reaction="loved"
                ),
                ChildActivity(
                    child_profile_id=aarav_id,
                    content_item_id="k-content-03",
                    activity_type="video",
                    dwell_time_seconds=240,
                    completed=True,
                    child_reaction="good"
                ),
                ChildActivity(
                    child_profile_id=aarav_id,
                    content_item_id="k-content-04",
                    activity_type="activity",
                    dwell_time_seconds=360,
                    completed=True,
                    child_reaction="loved"
                )
            ]
            db.add_all(seed_acts)
            db.commit()
            print("Seeded initial activities for Aarav.")

        # Seed initial achievements for Aarav
        achievs = db.query(ChildAchievement).filter(ChildAchievement.child_profile_id == aarav_id).all()
        if not achievs:
            seed_badges = [
                ChildAchievement(
                    child_profile_id=aarav_id,
                    badge_code="first_explorer",
                    title="Curious Explorer",
                    description="Began the learning journey on EduFeedia Kids!",
                    icon="🚀",
                    stars_awarded=5
                ),
                ChildAchievement(
                    child_profile_id=aarav_id,
                    badge_code="junior_scientist",
                    title="Junior Scientist",
                    description="Discovered how leaves drink sunlight!",
                    icon="🔬",
                    stars_awarded=5
                ),
                ChildAchievement(
                    child_profile_id=aarav_id,
                    badge_code="money_adventurer",
                    title="Money Adventurer",
                    description="Chose to save in the piggy bank during the ₹100 adventure!",
                    icon="💰",
                    stars_awarded=5
                )
            ]
            db.add_all(seed_badges)
            db.commit()
            print("Seeded initial badges for Aarav.")

        print("Kids ecosystem seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"Error seeding kids ecosystem: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_kids_ecosystem()
