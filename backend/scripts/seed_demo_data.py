"""
Development & Testing Demo Data Seeder for Edufeedia.
Builds demo schools, classes, students (Rahul, Priya, Aman, Sneha), teachers, parents,
progress history, and quiz attempts for local development and test fixtures.
DO NOT RUN IN PRODUCTION.
"""

import sys
import os
import datetime
from sqlalchemy.orm import Session
import bcrypt

# Add the backend folder to system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import engine, SessionLocal, Base
from app.models.models import (
    ContentItem, Quiz, Question, School, SchoolClass, User, StudentProfile,
    StudentProgress, QuizAttempt, SpacedRepetitionSchedule, Flashcard,
    Badge, UserBadge, ClassAssignment, parent_student_links, teacher_classes
)
from app.embeddings.embedder import embed_content
from app.core.excel_exporter import sync_database_to_excel

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def seed_demo_data():
    print("Seeding Edufeedia database with full test suite fixtures...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Add School
        school = School(
            name="Apex International Academy",
            domain="apexschool.edu",
            address="New Delhi, India"
        )
        db.add(school)
        db.flush()

        # Add Classes
        class_10a = SchoolClass(
            school_id=school.id,
            grade_level=10,
            section_name="A",
            academic_year="2026-2027"
        )
        class_9b = SchoolClass(
            school_id=school.id,
            grade_level=9,
            section_name="B",
            academic_year="2026-2027"
        )
        db.add_all([class_10a, class_9b])
        db.flush()

        # 2. Add Teacher User
        teacher_user = User(
            email="sharma@apexschool.edu",
            password_hash=get_password_hash("Teacher123!"),
            role="teacher",
            first_name="Sunita",
            last_name="Sharma",
            is_verified=True,
            school_id=school.id
        )
        db.add(teacher_user)
        db.flush()

        # Link teacher to classes
        db.execute(teacher_classes.insert().values(
            teacher_user_id=teacher_user.id,
            class_id=class_10a.id,
            subject="Mathematics & Science"
        ))
        db.execute(teacher_classes.insert().values(
            teacher_user_id=teacher_user.id,
            class_id=class_9b.id,
            subject="Computer Science & Coding"
        ))

        # 3. Add Students
        student_rahul = User(
            email="rahul@apexschool.edu",
            password_hash=get_password_hash("Student123!"),
            role="student",
            first_name="Rahul",
            last_name="Kumar",
            is_verified=True,
            school_id=school.id
        )
        student_priya = User(
            email="priya@apexschool.edu",
            password_hash=get_password_hash("Student123!"),
            role="student",
            first_name="Priya",
            last_name="Sharma",
            is_verified=True,
            school_id=school.id
        )
        student_aman = User(
            email="aman@apexschool.edu",
            password_hash=get_password_hash("Student123!"),
            role="student",
            first_name="Aman",
            last_name="Gupta",
            is_verified=True,
            school_id=school.id
        )
        student_sneha = User(
            email="sneha@apexschool.edu",
            password_hash=get_password_hash("Student123!"),
            role="student",
            first_name="Sneha",
            last_name="Patel",
            is_verified=True,
            school_id=school.id
        )
        db.add_all([student_rahul, student_priya, student_aman, student_sneha])
        db.flush()

        # Student Profiles with Verified Onboarding & Consent
        profile_rahul = StudentProfile(
            user_id=student_rahul.id,
            school_id=school.id,
            class_id=class_10a.id,
            board="CBSE",
            date_of_birth=datetime.date(2011, 5, 15),
            onboarding_status="COMPLETED",
            parental_consent_status="GRANTED",
            xp_score=350,
            streak_count=6,
            last_active_date=datetime.date.today(),
            interests=["Coding", "Science", "Space", "Mathematics"],
            learning_preference=["video", "reading"]
        )
        profile_priya = StudentProfile(
            user_id=student_priya.id,
            school_id=school.id,
            class_id=class_10a.id,
            board="CBSE",
            date_of_birth=datetime.date(2011, 3, 20),
            onboarding_status="COMPLETED",
            parental_consent_status="GRANTED",
            xp_score=520,
            streak_count=12,
            last_active_date=datetime.date.today(),
            interests=["Mathematics", "Physics", "Robotics"],
            learning_preference=["video", "interactive"]
        )
        profile_aman = StudentProfile(
            user_id=student_aman.id,
            school_id=school.id,
            class_id=class_10a.id,
            board="CBSE",
            date_of_birth=datetime.date(2011, 8, 10),
            onboarding_status="COMPLETED",
            parental_consent_status="GRANTED",
            xp_score=210,
            streak_count=3,
            last_active_date=datetime.date.today(),
            interests=["Coding", "Gaming", "Science"],
            learning_preference=["reading", "video"]
        )
        profile_sneha = StudentProfile(
            user_id=student_sneha.id,
            school_id=school.id,
            class_id=class_10a.id,
            board="CBSE",
            date_of_birth=datetime.date(2011, 11, 2),
            onboarding_status="COMPLETED",
            parental_consent_status="GRANTED",
            xp_score=95,
            streak_count=1,
            last_active_date=datetime.date.today(),
            interests=["Biology", "Chemistry"],
            learning_preference=["video"]
        )
        db.add_all([profile_rahul, profile_priya, profile_aman, profile_sneha])

        # 4. Add Parent & Admin Users
        admin_user = User(
            email="admin@apexschool.edu",
            password_hash=get_password_hash("Admin123!"),
            role="school_admin",
            first_name="Principal",
            last_name="Verma",
            is_verified=True,
            school_id=school.id
        )
        parent_user = User(
            email="parent@gmail.com",
            password_hash=get_password_hash("Parent123!"),
            role="parent",
            first_name="Rajesh",
            last_name="Kumar",
            is_verified=True
        )
        db.add_all([admin_user, parent_user])
        db.flush()

        # Link parent to Rahul
        db.execute(parent_student_links.insert().values(
            parent_user_id=parent_user.id,
            student_user_id=student_rahul.id,
            is_verified=True
        ))

        # 5. Add Badges
        badges = [
            Badge(
                code="streak_3",
                name="3-Day Momentum",
                description="Completed daily active learning revision for 3 consecutive days.",
                icon="fa-fire",
                category="streak",
                xp_bonus=30
            ),
            Badge(
                code="streak_7",
                name="7-Day Streak Warrior",
                description="Achieved an unbroken 7-day learning streak! Built consistent recall habit.",
                icon="fa-bolt",
                category="streak",
                xp_bonus=75
            ),
            Badge(
                code="quiz_100",
                name="Quiz Prodigy",
                description="Scored 100% accuracy on a curriculum evaluation quiz.",
                icon="fa-award",
                category="mastery",
                xp_bonus=50
            ),
            Badge(
                code="lesson_5",
                name="Knowledge Seeker",
                description="Completed 5 distinct curriculum learning modules.",
                icon="fa-book-open",
                category="progress",
                xp_bonus=45
            ),
            Badge(
                code="scholar_xp",
                name="Active Scholar",
                description="Surpassed 300 XP in learning achievements.",
                icon="fa-crown",
                category="level",
                xp_bonus=100
            ),
            Badge(
                code="stem_explorer",
                name="STEM Pioneer",
                description="Mastered topics across Mathematics, Science, and Coding.",
                icon="fa-atom",
                category="breadth",
                xp_bonus=60
            )
        ]
        db.add_all(badges)
        db.flush()

        # Grant initial badges
        db.add(UserBadge(user_id=student_rahul.id, badge_id=badges[0].id))
        db.add(UserBadge(user_id=student_rahul.id, badge_id=badges[4].id))
        db.add(UserBadge(user_id=student_priya.id, badge_id=badges[0].id))
        db.add(UserBadge(user_id=student_priya.id, badge_id=badges[1].id))
        db.add(UserBadge(user_id=student_priya.id, badge_id=badges[2].id))
        db.add(UserBadge(user_id=student_priya.id, badge_id=badges[4].id))

        # 6. Add Curated Educational Content Items with Embeddings
        content_items_data = [
            {
                "title": "Introduction to Quadratic Equations",
                "description": "Learn the standard form ax^2 + bx + c = 0, find roots using factorisation and formula methods, and solve real-world word problems.",
                "source_url": "https://www.youtube.com/embed/ZCcCyb-15P8",
                "source_platform": "YouTube Safe EDU",
                "embed_code": '<iframe width="560" height="315" src="https://www.youtube.com/embed/ZCcCyb-15P8" frameborder="0" allowfullscreen></iframe>',
                "type": "video",
                "board": "CBSE",
                "grade_level": 10,
                "subject": "Mathematics",
                "topic": "Quadratic Equations",
                "difficulty": "medium",
                "duration_minutes": 10,
                "tags": ["Math", "Algebra", "Quadratic Equations", "CBSE", "NCERT"],
                "safety_score": 99.5,
                "edu_score": 96.0,
                "is_approved": True
            },
            {
                "title": "Arithmetic Progressions: Formulas & Applications",
                "description": "Master AP sequence terms, the general nth term formula a_n = a + (n-1)d, and the sum of n terms S_n = n/2(2a + (n-1)d).",
                "source_url": "https://www.youtube.com/embed/1_j7i7D-oH8",
                "source_platform": "YouTube Safe EDU",
                "embed_code": '<iframe width="560" height="315" src="https://www.youtube.com/embed/1_j7i7D-oH8" frameborder="0" allowfullscreen></iframe>',
                "type": "video",
                "board": "CBSE",
                "grade_level": 10,
                "subject": "Mathematics",
                "topic": "Arithmetic Progressions",
                "difficulty": "easy",
                "duration_minutes": 12,
                "tags": ["Math", "Sequences", "Arithmetic Progressions", "CBSE", "Class 10"],
                "safety_score": 100.0,
                "edu_score": 94.0,
                "is_approved": True
            },
            {
                "title": "Human Respiration & Cellular Energy Production",
                "description": "Detailed biology breakdown of aerobic and anaerobic cellular respiration, glycolysis, ATP synthesis, and alveoli gas exchange.",
                "source_url": "https://www.youtube.com/embed/00jbG_cfGuQ",
                "source_platform": "YouTube Safe EDU",
                "embed_code": '<iframe width="560" height="315" src="https://www.youtube.com/embed/00jbG_cfGuQ" frameborder="0" allowfullscreen></iframe>',
                "type": "video",
                "board": "CBSE",
                "grade_level": 10,
                "subject": "Science",
                "topic": "Human Respiration",
                "difficulty": "medium",
                "duration_minutes": 14,
                "tags": ["Biology", "Respiration", "Life Processes", "ATP", "CBSE"],
                "safety_score": 99.8,
                "edu_score": 98.0,
                "is_approved": True
            },
            {
                "title": "Chemical Reactions & Equations",
                "description": "Types of chemical reactions: combination, decomposition, displacement, double displacement, redox, and balancing redox equations.",
                "source_url": "https://www.youtube.com/embed/g-bi_H833qE",
                "source_platform": "YouTube Safe EDU",
                "embed_code": '<iframe width="560" height="315" src="https://www.youtube.com/embed/g-bi_H833qE" frameborder="0" allowfullscreen></iframe>',
                "type": "video",
                "board": "CBSE",
                "grade_level": 10,
                "subject": "Science",
                "topic": "Chemical Reactions",
                "difficulty": "medium",
                "duration_minutes": 11,
                "tags": ["Chemistry", "Reactions", "Equations", "CBSE", "NCERT"],
                "safety_score": 99.0,
                "edu_score": 95.0,
                "is_approved": True
            },
            {
                "title": "Newton's Laws of Motion & Momentum",
                "description": "Foundational physics exploring inertia, F = ma, action-reaction pairs, and the law of conservation of linear momentum.",
                "source_url": "https://www.youtube.com/embed/kKKM8Y-u7ds",
                "source_platform": "YouTube Safe EDU",
                "embed_code": '<iframe width="560" height="315" src="https://www.youtube.com/embed/kKKM8Y-u7ds" frameborder="0" allowfullscreen></iframe>',
                "type": "video",
                "board": "CBSE",
                "grade_level": 10,
                "subject": "Science",
                "topic": "Newton's Laws",
                "difficulty": "hard",
                "duration_minutes": 15,
                "tags": ["Physics", "Mechanics", "Force", "Newton", "Momentum"],
                "safety_score": 100.0,
                "edu_score": 97.0,
                "is_approved": True
            },
            {
                "title": "Python Functions & Modular Programming",
                "description": "Introduction to Python def keyword, parameters, return values, scope, and building modular algorithms.",
                "source_url": "https://www.youtube.com/embed/u-OmVr_fT4s",
                "source_platform": "YouTube Safe EDU",
                "embed_code": '<iframe width="560" height="315" src="https://www.youtube.com/embed/u-OmVr_fT4s" frameborder="0" allowfullscreen></iframe>',
                "type": "video",
                "board": "CBSE",
                "grade_level": 10,
                "subject": "Coding",
                "topic": "Python Functions",
                "difficulty": "easy",
                "duration_minutes": 10,
                "tags": ["Computer Science", "Python", "Coding", "Functions", "Programming"],
                "safety_score": 100.0,
                "edu_score": 99.0,
                "is_approved": True
            },
            {
                "title": "Black Holes & Gravitational Physics",
                "description": "Astrophysics exploration of stellar evolution, event horizons, singularity, and general relativity.",
                "source_url": "https://www.youtube.com/embed/e-P5IFTqB98",
                "source_platform": "YouTube Safe EDU",
                "embed_code": '<iframe width="560" height="315" src="https://www.youtube.com/embed/e-P5IFTqB98" frameborder="0" allowfullscreen></iframe>',
                "type": "video",
                "board": "CBSE",
                "grade_level": 10,
                "subject": "Space",
                "topic": "Black Holes",
                "difficulty": "hard",
                "duration_minutes": 16,
                "tags": ["Astronomy", "Space", "Black Holes", "Physics", "Relativity"],
                "safety_score": 100.0,
                "edu_score": 98.0,
                "is_approved": True
            },
            {
                "title": "Introduction to Computer Networks & Topologies",
                "description": "Foundational computer network architectures, packet routing, and network topologies.",
                "source_url": "https://www.youtube.com/embed/network_101",
                "source_platform": "YouTube Safe EDU",
                "embed_code": '<iframe width="560" height="315" src="https://www.youtube.com/embed/network_101" frameborder="0" allowfullscreen></iframe>',
                "type": "video",
                "board": "CBSE",
                "grade_level": 10,
                "subject": "Computer Science",
                "topic": "Computer Networks",
                "difficulty": "medium",
                "duration_minutes": 12,
                "tags": ["Computer Science", "network", "Coding", "Internet", "Topologies"],
                "safety_score": 100.0,
                "edu_score": 96.0,
                "is_approved": True
            }
        ]

        saved_items = []
        for d in content_items_data:
            emb = embed_content(d["title"], d["description"], d["subject"], d["topic"], d["tags"])
            item = ContentItem(
                title=d["title"],
                description=d["description"],
                source_url=d["source_url"],
                source_platform=d["source_platform"],
                embed_code=d["embed_code"],
                type=d["type"],
                board=d["board"],
                grade_level=d["grade_level"],
                subject=d["subject"],
                topic=d["topic"],
                difficulty=d["difficulty"],
                duration_minutes=d["duration_minutes"],
                tags=d["tags"],
                safety_score=d["safety_score"],
                edu_score=d["edu_score"],
                is_approved=d["is_approved"],
                embedding=emb
            )
            db.add(item)
            saved_items.append(item)

        db.flush()

        # 7. Quizzes
        q1 = Quiz(content_item_id=saved_items[0].id, title="Quadratic Equations Mastery Check")
        db.add(q1)
        db.flush()
        db.add_all([
            Question(
                quiz_id=q1.id,
                question_text="What is the standard form of a quadratic equation in one variable?",
                options=["ax + b = 0", "ax² + bx + c = 0", "ax³ + bx² + c = 0", "a/x + b = c"],
                correct_answer="ax² + bx + c = 0",
                explanation="A quadratic equation is a second-degree polynomial equation with standard form ax² + bx + c = 0, where a ≠ 0.",
                difficulty="easy"
            ),
            Question(
                quiz_id=q1.id,
                question_text="What does the discriminant D = b² - 4ac reveal when D > 0?",
                options=["Two distinct real roots", "Two equal real roots", "No real roots", "Zero roots"],
                correct_answer="Two distinct real roots",
                explanation="When D > 0, the quadratic formula yields two distinct real values for x.",
                difficulty="medium"
            )
        ])

        # 8. Flashcards
        flashcards = [
            Flashcard(
                subject="Mathematics",
                topic="Quadratic Equations",
                front_text="What is the quadratic formula to find roots of ax² + bx + c = 0?",
                back_text="x = (-b ± √(b² - 4ac)) / (2a)",
                hint="Remember the discriminant inside the square root.",
                grade_level=10,
                board="CBSE"
            ),
            Flashcard(
                subject="Mathematics",
                topic="Arithmetic Progressions",
                front_text="What is the formula for the nth term of an Arithmetic Progression?",
                back_text="aₙ = a + (n - 1)d\n(where a = first term, d = common difference)",
                hint="Add (n - 1) common differences to the first term.",
                grade_level=10,
                board="CBSE"
            ),
            Flashcard(
                subject="Science",
                topic="Human Respiration",
                front_text="What is the balanced equation for aerobic cellular respiration?",
                back_text="C₆H₁₂O₆ + 6O₂ ➔ 6CO₂ + 6H₂O + 38 ATP",
                hint="Glucose and oxygen react to produce carbon dioxide, water, and energy.",
                grade_level=10,
                board="CBSE"
            ),
            Flashcard(
                subject="Coding",
                topic="Python Functions",
                front_text="What is the difference between *args and **kwargs in Python function parameters?",
                back_text="*args accepts variable positional arguments as a tuple.\n**kwargs accepts keyword arguments as a dictionary.",
                hint="One creates a tuple, the other creates a dict.",
                grade_level=10,
                board="CBSE"
            )
        ]
        db.add_all(flashcards)

        # 9. Mock Student Progress
        now = datetime.datetime.now(datetime.UTC)
        db.add_all([
            StudentProgress(
                student_user_id=student_rahul.id,
                content_item_id=saved_items[0].id,
                progress_percentage=100,
                completed_at=now - datetime.timedelta(days=1)
            ),
            StudentProgress(
                student_user_id=student_rahul.id,
                content_item_id=saved_items[5].id,
                progress_percentage=100,
                completed_at=now
            ),
            StudentProgress(
                student_user_id=student_priya.id,
                content_item_id=saved_items[0].id,
                progress_percentage=100,
                completed_at=now - datetime.timedelta(days=1)
            ),
            StudentProgress(
                student_user_id=student_priya.id,
                content_item_id=saved_items[2].id,
                progress_percentage=100,
                completed_at=now
            )
        ])

        # 10. Mock Quiz Attempts
        db.add_all([
            QuizAttempt(
                student_user_id=student_rahul.id,
                quiz_id=q1.id,
                attempt_number=1,
                score=2,
                max_score=2,
                accuracy_percentage=100.0,
                completed_at=now - datetime.timedelta(days=1)
            ),
            QuizAttempt(
                student_user_id=student_priya.id,
                quiz_id=q1.id,
                attempt_number=1,
                score=2,
                max_score=2,
                accuracy_percentage=100.0,
                completed_at=now - datetime.timedelta(days=1)
            )
        ])

        # 11. Mock Assignments
        db.add(ClassAssignment(
            teacher_user_id=teacher_user.id,
            class_id=class_10a.id,
            content_item_id=saved_items[0].id,
            quiz_id=q1.id,
            title="Quadratic Equations Weekly Homework",
            instructions="Watch video and complete the 2-question concept review.",
            due_date=datetime.date.today() + datetime.timedelta(days=3)
        ))

        db.commit()
        print("Seeding complete! Database records exported to Excel sheet: edufeedia_database_records.xlsx")
        try:
            excel_path = sync_database_to_excel(db)
            print(f"Excel snapshot: {excel_path}")
        except Exception:
            pass

    except Exception as e:
        db.rollback()
        print(f"[Demo Seeder Error]: {e}")
        raise
    finally:
        db.close()

# Backwards compatibility alias
seed_database = seed_demo_data

if __name__ == "__main__":
    seed_demo_data()
