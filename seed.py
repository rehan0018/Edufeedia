import sys
import os
import datetime
from sqlalchemy.orm import Session
import bcrypt

# Add the backend folder to system path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.database import engine, SessionLocal, Base
from app.models.models import (
    ContentItem, Quiz, Question, School, SchoolClass, User, StudentProfile,
    StudentProgress, QuizAttempt, SpacedRepetitionSchedule, Flashcard,
    Badge, UserBadge, ClassAssignment, parent_student_links, teacher_classes
)

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def seed_database():
    print("Seeding Edufeedia database with full test suite fixtures...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 2. Add School
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

    # 3. Add Teacher User
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

    # 4. Add Students
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

    # Student Profiles
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

    # 5. Add Parent & Admin Users
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

    # 6. Add Badges
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

    # Grant initial badges to Rahul and Priya
    db.add(UserBadge(user_id=student_rahul.id, badge_id=badges[0].id)) # streak_3
    db.add(UserBadge(user_id=student_rahul.id, badge_id=badges[4].id)) # scholar_xp
    db.add(UserBadge(user_id=student_priya.id, badge_id=badges[0].id))
    db.add(UserBadge(user_id=student_priya.id, badge_id=badges[1].id)) # streak_7
    db.add(UserBadge(user_id=student_priya.id, badge_id=badges[2].id)) # quiz_100
    db.add(UserBadge(user_id=student_priya.id, badge_id=badges[4].id))

    # 7. Add Curated Educational Content Items
    # Math: Quadratic Equations
    item_math1 = ContentItem(
        title="Introduction to Quadratic Equations",
        description="Learn the standard form ax^2 + bx + c = 0, find roots using factorisation and formula methods, and solve real-world word problems.",
        source_url="https://www.youtube.com/embed/ZCcCyb-15P8",
        source_platform="YouTube Safe EDU",
        embed_code='<iframe width="560" height="315" src="https://www.youtube.com/embed/ZCcCyb-15P8" frameborder="0" allowfullscreen></iframe>',
        type="video",
        board="CBSE",
        grade_level=10,
        subject="Mathematics",
        topic="Quadratic Equations",
        difficulty="medium",
        duration_minutes=10,
        safety_score=100,
        edu_score=98,
        is_approved=True
    )
    # Math: Arithmetic Progressions
    item_math2 = ContentItem(
        title="Arithmetic Progressions: nth Term & Sum Formula",
        description="Understanding common difference 'd', calculating any arbitrary term using an = a + (n-1)d, and computing summation Sn = n/2 [2a + (n-1)d].",
        source_url="https://www.khanacademy.org/math/in-in-grade-10-ncert/x573d8ce2:arithmetic-progressions",
        source_platform="NCERT Academy",
        embed_code=None,
        type="reading",
        board="CBSE",
        grade_level=10,
        subject="Mathematics",
        topic="Arithmetic Progressions",
        difficulty="easy",
        duration_minutes=8,
        safety_score=100,
        edu_score=96,
        is_approved=True
    )
    # Science: Human Respiration
    item_sci1 = ContentItem(
        title="Human Respiration Process Explained",
        description="Detailing aerobic vs anaerobic respiration, structure of alveoli, gaseous exchange, and how cellular energy (ATP) is generated.",
        source_url="https://www.youtube.com/embed/3nL2_O1wZ5Y",
        source_platform="YouTube Safe EDU",
        embed_code='<iframe width="560" height="315" src="https://www.youtube.com/embed/3nL2_O1wZ5Y" frameborder="0" allowfullscreen></iframe>',
        type="video",
        board="CBSE",
        grade_level=10,
        subject="Science",
        topic="Human Respiration",
        difficulty="medium",
        duration_minutes=12,
        safety_score=100,
        edu_score=95,
        is_approved=True
    )
    # Science: Periodic Table & Chemical Bonding
    item_sci2 = ContentItem(
        title="Periodic Classification & Chemical Bonding",
        description="Explore Mendeleev and Modern Periodic Tables, periodic trends (electronegativity, atomic radius), and ionic vs covalent bonds.",
        source_url="https://www.youtube.com/embed/0RRVV4Diomg",
        source_platform="YouTube Safe EDU",
        embed_code='<iframe width="560" height="315" src="https://www.youtube.com/embed/0RRVV4Diomg" frameborder="0" allowfullscreen></iframe>',
        type="video",
        board="CBSE",
        grade_level=10,
        subject="Science",
        topic="Chemical Bonding",
        difficulty="hard",
        duration_minutes=14,
        safety_score=100,
        edu_score=97,
        is_approved=True
    )
    # Science: Newton's Laws
    item_sci3 = ContentItem(
        title="Newton's Laws of Motion & Momentum Recall",
        description="Core breakdown of inertia (First Law), F = ma (Second Law), action-reaction pairs (Third Law), and conservation of linear momentum.",
        source_url="https://www.physicsclassroom.com/class/newtlaws",
        source_platform="Physics Classroom",
        embed_code=None,
        type="reading",
        board="CBSE",
        grade_level=10,
        subject="Science",
        topic="Newton's Laws",
        difficulty="medium",
        duration_minutes=6,
        safety_score=100,
        edu_score=94,
        is_approved=True
    )
    # Coding: Python Functions
    item_code1 = ContentItem(
        title="Understanding Python Functions & Scope",
        description="A gentle intro to modular programming, def keyword, parameter scopes, arguments, return statements, and clean function documentation.",
        source_url="https://www.youtube.com/embed/9Os0o3wzS_I",
        source_platform="YouTube Safe EDU",
        embed_code='<iframe width="560" height="315" src="https://www.youtube.com/embed/9Os0o3wzS_I" frameborder="0" allowfullscreen></iframe>',
        type="video",
        board="CBSE",
        grade_level=10,
        subject="Coding",
        topic="Python Functions",
        difficulty="easy",
        duration_minutes=15,
        safety_score=100,
        edu_score=99,
        is_approved=True
    )
    # Coding: AI & Neural Networks
    item_code2 = ContentItem(
        title="Introduction to Artificial Intelligence & Neural Networks",
        description="Learn how computers recognize patterns, what machine learning models do, training with data, and ethical considerations for safe AI.",
        source_url="https://www.elements-of-ai.com",
        source_platform="Open Educational Resources",
        embed_code=None,
        type="reading",
        board="CBSE",
        grade_level=10,
        subject="Coding",
        topic="AI Fundamentals",
        difficulty="medium",
        duration_minutes=10,
        safety_score=100,
        edu_score=98,
        is_approved=True
    )
    # Space: Black Holes
    item_space = ContentItem(
        title="Mysteries of Black Holes & Event Horizons",
        description="How massive stars collapse, gravitational singularities, Hawking radiation, and how astronomers image black holes with the Event Horizon Telescope.",
        source_url="https://www.youtube.com/embed/e-P5IFTqB98",
        source_platform="NASA Safe Space Lab",
        embed_code='<iframe width="560" height="315" src="https://www.youtube.com/embed/e-P5IFTqB98" frameborder="0" allowfullscreen></iframe>',
        type="video",
        board="CBSE",
        grade_level=10,
        subject="Space",
        topic="Black Holes",
        difficulty="medium",
        duration_minutes=11,
        safety_score=100,
        edu_score=96,
        is_approved=True
    )

    # Computer Science: Computer Networks & Topologies
    item_cs_net1 = ContentItem(
        title="Introduction to Computer Networks & Topologies",
        description="Core principles of node interconnectivity, Star/Bus/Mesh topologies, guided vs unguided transmission, and LAN vs WAN geographic classification.",
        source_url="https://www.youtube.com/embed/3QhU9jd03a0",
        source_platform="YouTube Safe EDU",
        embed_code='<iframe width="560" height="315" src="https://www.youtube.com/embed/3QhU9jd03a0" frameborder="0" allowfullscreen></iframe>',
        type="video",
        board="CBSE",
        grade_level=10,
        subject="Computer Science",
        topic="Computer Networks",
        difficulty="easy",
        duration_minutes=12,
        safety_score=100,
        edu_score=98,
        is_approved=True
    )

    # Computer Science: OSI Model & Protocols
    item_cs_net2 = ContentItem(
        title="The OSI 7-Layer Model & Internet Protocols",
        description="Comprehensive guide through Physical, Data Link, Network (IP), Transport (TCP/UDP), and Application layers with packet encapsulation.",
        source_url="https://www.youtube.com/embed/IPvYjXCsTg8",
        source_platform="YouTube Safe EDU",
        embed_code='<iframe width="560" height="315" src="https://www.youtube.com/embed/IPvYjXCsTg8" frameborder="0" allowfullscreen></iframe>',
        type="video",
        board="CBSE",
        grade_level=10,
        subject="Computer Science",
        topic="Computer Networks",
        difficulty="medium",
        duration_minutes=14,
        safety_score=100,
        edu_score=99,
        is_approved=True
    )

    # Science: Electricity & Circuits
    item_sci_elec = ContentItem(
        title="Electricity, Ohm's Law & Circuit Analysis",
        description="Master potential difference (V), electric current (I), Ohm's law (V = IR), and calculating equivalent resistance for series and parallel resistor circuits.",
        source_url="https://www.youtube.com/embed/hsglQ3PfG8I",
        source_platform="YouTube Safe EDU",
        embed_code='<iframe width="560" height="315" src="https://www.youtube.com/embed/hsglQ3PfG8I" frameborder="0" allowfullscreen></iframe>',
        type="video",
        board="CBSE",
        grade_level=10,
        subject="Science",
        topic="Electricity & Circuits",
        difficulty="medium",
        duration_minutes=15,
        safety_score=100,
        edu_score=97,
        is_approved=True
    )

    # Mathematics: Trigonometry
    item_math_trig = ContentItem(
        title="Introduction to Trigonometric Ratios & Identities",
        description="Understanding right triangle side ratios (sine, cosine, tangent), standard angles (30°, 45°, 60°), and key identity sin²(θ) + cos²(θ) = 1.",
        source_url="https://www.youtube.com/embed/PUB0TaZ7bhA",
        source_platform="YouTube Safe EDU",
        embed_code='<iframe width="560" height="315" src="https://www.youtube.com/embed/PUB0TaZ7bhA" frameborder="0" allowfullscreen></iframe>',
        type="video",
        board="CBSE",
        grade_level=10,
        subject="Mathematics",
        topic="Trigonometry",
        difficulty="medium",
        duration_minutes=16,
        safety_score=100,
        edu_score=96,
        is_approved=True
    )

    db.add_all([
        item_math1, item_math2, item_sci1, item_sci2, item_sci3,
        item_code1, item_code2, item_space, item_cs_net1, item_cs_net2,
        item_sci_elec, item_math_trig
    ])
    db.flush()

    # 8. Add Quizzes & Questions
    # Quiz: Computer Networks (Topologies & Fundamentals)
    quiz_net1 = Quiz(content_item_id=item_cs_net1.id, title="Computer Networks Foundations Quiz")
    db.add(quiz_net1)
    db.flush()
    db.add_all([
        Question(
            quiz_id=quiz_net1.id,
            question_text="Which network topology connects every node to a central device (like a switch or hub)?",
            options=["Star Topology", "Bus Topology", "Ring Topology", "Mesh Topology"],
            correct_answer="Star Topology",
            explanation="In a star topology, all peripheral devices connect point-to-point to a central hub or switch.",
            difficulty="easy"
        ),
        Question(
            quiz_id=quiz_net1.id,
            question_text="What is the primary geographic distinction between a LAN and a WAN?",
            options=[
                "LAN covers a local room or building, whereas WAN spans across cities, countries, or continents",
                "LAN is only wireless while WAN is only wired",
                "LAN uses satellite connections while WAN uses Ethernet cables",
                "LAN is publicly accessible while WAN is strictly private"
            ],
            correct_answer="LAN covers a local room or building, whereas WAN spans across cities, countries, or continents",
            explanation="Local Area Networks (LAN) operate within limited geographical areas (e.g. school/home), whereas Wide Area Networks (WAN) cover global distances.",
            difficulty="easy"
        ),
        Question(
            quiz_id=quiz_net1.id,
            question_text="What is the role of a Router in a computer network?",
            options=[
                "Forwards data packets across different IP subnets to find the optimal path",
                "Displays graphics on the user's computer monitor",
                "Stores HTML files permanently on a hard drive",
                "Converts software source code into binary machine instructions"
            ],
            correct_answer="Forwards data packets across different IP subnets to find the optimal path",
            explanation="Routers operate at the Network Layer (Layer 3) to route IP packets between separate networks.",
            difficulty="medium"
        )
    ])

    # Quiz: Electricity & Circuits
    quiz_elec = Quiz(content_item_id=item_sci_elec.id, title="Electricity & Circuits Diagnostic")
    db.add(quiz_elec)
    db.flush()
    db.add_all([
        Question(
            quiz_id=quiz_elec.id,
            question_text="What is the mathematical equation representing Ohm's Law?",
            options=["V = I * R", "P = V * I", "E = m * c^2", "F = m * a"],
            correct_answer="V = I * R",
            explanation="Ohm's law states Voltage (V) equals Current (I) multiplied by Resistance (R).",
            difficulty="easy"
        ),
        Question(
            quiz_id=quiz_elec.id,
            question_text="In a parallel circuit with two identical 10-Ohm resistors, what is the equivalent total resistance?",
            options=["5 Ohms", "20 Ohms", "10 Ohms", "15 Ohms"],
            correct_answer="5 Ohms",
            explanation="For parallel resistors: 1/R_eq = 1/10 + 1/10 = 2/10 = 1/5 -> R_eq = 5 Ohms.",
            difficulty="medium"
        )
    ])

    # Quiz 1: Math (Quadratic Equations)
    quiz_math1 = Quiz(content_item_id=item_math1.id, title="Quadratic Equations Mastery Check")
    db.add(quiz_math1)
    db.flush()
    db.add_all([
        Question(
            quiz_id=quiz_math1.id,
            question_text="What is the standard form of a quadratic equation?",
            options=["ax + b = 0", "ax^2 + bx + c = 0", "ax^3 + bx^2 + cx + d = 0", "y = mx + c"],
            correct_answer="ax^2 + bx + c = 0",
            explanation="Standard quadratic form requires the highest degree term to be squared (power 2).",
            difficulty="easy"
        ),
        Question(
            quiz_id=quiz_math1.id,
            question_text="If the discriminant (b^2 - 4ac) is positive (> 0), what is the nature of the roots?",
            options=["Real and equal", "Real and distinct", "Complex / Imaginary", "No roots exist"],
            correct_answer="Real and distinct",
            explanation="A discriminant strictly greater than zero yields two distinct real numbers as solutions.",
            difficulty="medium"
        ),
        Question(
            quiz_id=quiz_math1.id,
            question_text="Solve the equation x^2 - 5x + 6 = 0.",
            options=["x = 1, 6", "x = 2, 3", "x = -2, -3", "x = -1, -6"],
            correct_answer="x = 2, 3",
            explanation="Factorising the expression gives (x - 2)(x - 3) = 0, so roots are x = 2 and x = 3.",
            difficulty="easy"
        )
    ])

    # Quiz 2: Science (Human Respiration)
    quiz_sci1 = Quiz(content_item_id=item_sci1.id, title="Respiration Dynamics Check")
    db.add(quiz_sci1)
    db.flush()
    db.add_all([
        Question(
            quiz_id=quiz_sci1.id,
            question_text="Which gas is released as a byproduct during cellular respiration?",
            options=["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"],
            correct_answer="Carbon Dioxide",
            explanation="During cellular respiration, oxygen reacts with glucose to produce carbon dioxide, water, and ATP.",
            difficulty="easy"
        ),
        Question(
            quiz_id=quiz_sci1.id,
            question_text="Where does the initial step of respiration (glycolysis) take place?",
            options=["Mitochondria", "Cytoplasm", "Alveoli", "Ribosomes"],
            correct_answer="Cytoplasm",
            explanation="Glycolysis takes place in the cytoplasm, while the Krebs cycle happens in the mitochondria.",
            difficulty="medium"
        ),
        Question(
            quiz_id=quiz_sci1.id,
            question_text="What is the universal energy currency produced during cellular respiration?",
            options=["DNA", "RNA", "ATP", "Glucose"],
            correct_answer="ATP",
            explanation="ATP (Adenosine Triphosphate) stores energy for biological reactions in living cells.",
            difficulty="easy"
        )
    ])

    # Quiz 3: Coding (Python Functions)
    quiz_code1 = Quiz(content_item_id=item_code1.id, title="Python Functions Core Check")
    db.add(quiz_code1)
    db.flush()
    db.add_all([
        Question(
            quiz_id=quiz_code1.id,
            question_text="Which keyword is used to declare a function in Python?",
            options=["function", "fun", "def", "define"],
            correct_answer="def",
            explanation="Python uses the keyword 'def' to define reusable function blocks.",
            difficulty="easy"
        ),
        Question(
            quiz_id=quiz_code1.id,
            question_text="What does a Python function return if no explicit return statement is present?",
            options=["0", "None", "False", "Undefined"],
            correct_answer="None",
            explanation="Python functions implicitly return the singleton object 'None' when reaching the end of the block.",
            difficulty="medium"
        ),
        Question(
            quiz_id=quiz_code1.id,
            question_text="How do you pass arguments into a function named 'calculate'?",
            options=["calculate(10)", "calculate 10", "call calculate(10)", "calculate.run(10)"],
            correct_answer="calculate(10)",
            explanation="Functions are called using parentheses containing any necessary positional or keyword arguments.",
            difficulty="easy"
        )
    ])

    # Quiz 4: Physics Recall
    quiz_phys = Quiz(content_item_id=item_sci3.id, title="Newton's Laws Quick Recall")
    db.add(quiz_phys)
    db.flush()
    db.add_all([
        Question(
            quiz_id=quiz_phys.id,
            question_text="Which law states that an object remains at rest unless acted upon by an external unbalanced force?",
            options=["First Law (Inertia)", "Second Law", "Third Law", "Law of Universal Gravitation"],
            correct_answer="First Law (Inertia)",
            explanation="Newton's First Law (Law of Inertia) establishes that velocity changes require net force.",
            difficulty="easy"
        ),
        Question(
            quiz_id=quiz_phys.id,
            question_text="What mathematical equation represents Newton's Second Law?",
            options=["F = m/a", "F = ma", "F = mv", "F = m^2a"],
            correct_answer="F = ma",
            explanation="Force = Mass x Acceleration (F = ma) formalizes the relationship in Newtonian mechanics.",
            difficulty="easy"
        )
    ])

    # 9. Add Flashcards for Active Recall Decks
    flashcards = [
        Flashcard(
            subject="Mathematics",
            topic="Quadratic Equations",
            front_text="What is the quadratic formula to find roots of ax² + bx + c = 0?",
            back_text="x = (-b ± √(b² - 4ac)) / (2a)",
            hint="Think of the discriminant under the square root sign.",
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
            subject="Science",
            topic="Chemical Bonding",
            front_text="What is the fundamental difference between Ionic and Covalent bonds?",
            back_text="Ionic bonds involve complete transfer of electrons between atoms (e.g. NaCl), while Covalent bonds involve sharing of electron pairs (e.g. H₂O).",
            hint="Transfer vs. sharing of valence electrons.",
            grade_level=10,
            board="CBSE"
        ),
        Flashcard(
            subject="Science",
            topic="Newton's Laws",
            front_text="State Newton's Third Law of Motion with an everyday example.",
            back_text="For every action, there is an equal and opposite reaction.\nExample: When a swimmer pushes water backward, the water propels them forward.",
            hint="Action and reaction forces occur on different interacting bodies.",
            grade_level=10,
            board="CBSE"
        ),
        Flashcard(
            subject="Coding",
            topic="Python Functions",
            front_text="What is the difference between *args and **kwargs in Python function parameters?",
            back_text="*args accepts an arbitrary number of positional arguments (as a tuple).\n**kwargs accepts an arbitrary number of keyword arguments (as a dictionary).",
            hint="One creates a tuple, the other creates key-value pairs (dict).",
            grade_level=10,
            board="CBSE"
        ),
        Flashcard(
            subject="Space",
            topic="Black Holes",
            front_text="What is the 'Event Horizon' of a Black Hole?",
            back_text="The boundary around a black hole beyond which nothing—not even light—can escape the gravitational pull.",
            hint="The point of no return.",
            grade_level=10,
            board="CBSE"
        )
    ]
    db.add_all(flashcards)

    # 10. Pre-populate Sample Progress & Quiz Attempts for Rahul & Priya
    # Rahul has completed Math1 & Sci1, and attempted quizzes
    progress_rahul_1 = StudentProgress(
        student_user_id=student_rahul.id,
        content_item_id=item_math1.id,
        progress_percentage=100,
        completed_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)
    )
    progress_rahul_2 = StudentProgress(
        student_user_id=student_rahul.id,
        content_item_id=item_sci1.id,
        progress_percentage=100,
        completed_at=datetime.datetime.utcnow()
    )
    db.add_all([progress_rahul_1, progress_rahul_2])

    attempt_rahul_1 = QuizAttempt(
        student_user_id=student_rahul.id,
        quiz_id=quiz_math1.id,
        score=3,
        max_score=3,
        accuracy_percentage=100.0,
        completed_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)
    )
    attempt_rahul_2 = QuizAttempt(
        student_user_id=student_rahul.id,
        quiz_id=quiz_sci1.id,
        score=2,
        max_score=3,
        accuracy_percentage=66.67,
        completed_at=datetime.datetime.utcnow()
    )
    db.add_all([attempt_rahul_1, attempt_rahul_2])

    # Spaced Repetition Schedule for Rahul
    sched_rahul_1 = SpacedRepetitionSchedule(
        student_user_id=student_rahul.id,
        subject="Mathematics",
        topic="Quadratic Equations",
        interval_days=6,
        repetition_number=2,
        easiness_factor=2.60,
        next_review_date=datetime.date.today() + datetime.timedelta(days=6)
    )
    sched_rahul_2 = SpacedRepetitionSchedule(
        student_user_id=student_rahul.id,
        subject="Science",
        topic="Human Respiration",
        interval_days=1,
        repetition_number=1,
        easiness_factor=2.36,
        next_review_date=datetime.date.today() # Due today for review!
    )
    db.add_all([sched_rahul_1, sched_rahul_2])

    # 11. Add Teacher Class Assignment
    assignment_1 = ClassAssignment(
        teacher_user_id=teacher_user.id,
        class_id=class_10a.id,
        content_item_id=item_sci2.id,
        quiz_id=quiz_sci1.id,
        title="Weekly Assignment: Chemical Bonding & Cellular Energy",
        instructions="Watch the video on Periodic Trends and review the respiration dynamic questions before Friday's lab.",
        due_date=datetime.date.today() + datetime.timedelta(days=5)
    )
    db.add(assignment_1)

    # 12. Compute Semantic Embeddings & Safety Labels for Content Items
    from app.embeddings.embedder import embed_content
    from app.safety.engine import SafetyEngine

    all_content = [item_math1, item_math2, item_sci1, item_sci2, item_sci3, item_code1, item_code2, item_space]
    for c in all_content:
        c.embedding = embed_content(c.title, c.description, c.subject, c.topic, c.tags)
        audit = SafetyEngine.audit_content(c.title, c.description or "", c.tags)
        c.safety_labels = audit
        c.safety_score = audit["safety_score"]

    # 13. Add User Interactions (Collaborative Behavioral Feedback)
    from app.models.models import UserInteraction
    interactions = [
        # Priya's interactions (Math, Coding, Physics)
        UserInteraction(user_id=student_priya.id, content_item_id=item_math1.id, interaction_type="completed", weight=5.0),
        UserInteraction(user_id=student_priya.id, content_item_id=item_math2.id, interaction_type="bookmark", weight=4.0),
        UserInteraction(user_id=student_priya.id, content_item_id=item_code1.id, interaction_type="like", weight=3.0),
        UserInteraction(user_id=student_priya.id, content_item_id=item_code2.id, interaction_type="view", weight=1.0),
        # Aman's interactions (Coding, Science)
        UserInteraction(user_id=student_aman.id, content_item_id=item_code1.id, interaction_type="completed", weight=5.0),
        UserInteraction(user_id=student_aman.id, content_item_id=item_code2.id, interaction_type="bookmark", weight=4.0),
        UserInteraction(user_id=student_aman.id, content_item_id=item_space.id, interaction_type="like", weight=3.0),
        # Rahul's past interactions
        UserInteraction(user_id=student_rahul.id, content_item_id=item_math1.id, interaction_type="completed", weight=5.0),
        UserInteraction(user_id=student_rahul.id, content_item_id=item_sci1.id, interaction_type="completed", weight=5.0),
        UserInteraction(user_id=student_rahul.id, content_item_id=item_code1.id, interaction_type="like", weight=3.0),
    ]
    db.add_all(interactions)

    db.commit()

    # 14. Export to Read-Only Excel Spreadsheet for Owner Audit
    from app.core.excel_exporter import sync_database_to_excel
    excel_file = sync_database_to_excel(db)
    print(f"Seeding complete! Database records exported to Excel sheet: {excel_file}")
    db.close()

if __name__ == "__main__":
    seed_database()
