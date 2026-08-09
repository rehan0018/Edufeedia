import sys
import os
import datetime
from sqlalchemy.orm import Session
import bcrypt

# Add the backend folder to system path to import modules
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.database import engine, SessionLocal, Base
from app.models.models import ContentItem, Quiz, Question, School, SchoolClass, User, StudentProfile, parent_student_links

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def seed_database():
    print("Seeding database...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # 1. Clear existing seed data to ensure fresh insert
    db.query(Question).delete()
    db.query(Quiz).delete()
    db.query(StudentProfile).delete()
    db.query(User).delete()
    db.query(SchoolClass).delete()
    db.query(School).delete()
    db.commit()

    # 2. Add a default school and class for student enrollment
    school = School(
        name="Apex International Academy",
        domain="apexschool.edu",
        address="New Delhi, India"
    )
    db.add(school)
    db.flush()

    school_class = SchoolClass(
        school_id=school.id,
        grade_level=10,
        section_name="A",
        academic_year="2026-2027"
    )
    db.add(school_class)
    db.flush()

    # 3. Add Default Student User
    student_user = User(
        email="rahul@apexschool.edu",
        password_hash=get_password_hash("Student123!"),
        role="student",
        first_name="Rahul",
        last_name="Kumar",
        is_verified=True,
        school_id=school.id
    )
    db.add(student_user)
    db.flush()

    student_profile = StudentProfile(
        user_id=student_user.id,
        school_id=school.id,
        class_id=school_class.id,
        board="CBSE",
        date_of_birth=datetime.date(2011, 5, 15),
        xp_score=350,  # Pre-populated mock progress
        streak_count=6,
        interests=["Coding", "Science", "Space"],
        learning_preference=["video", "reading"]
    )
    db.add(student_profile)

    # 4. Add Default Parent User
    parent_user = User(
        email="parent@gmail.com",
        password_hash=get_password_hash("Parent123!"),
        role="parent",
        first_name="Rajesh",
        last_name="Kumar",
        is_verified=True
    )
    db.add(parent_user)
    db.flush()

    # Link parent and student
    assoc = parent_student_links.insert().values(
        parent_user_id=parent_user.id,
        student_user_id=student_user.id,
        is_verified=True
    )
    db.execute(assoc)

    # 5. Add Content Items
    # Item 1: Math (Quadratic Equations)
    item_math = ContentItem(
        title="Introduction to Quadratic Equations",
        description="Learn the standard form ax^2 + bx + c = 0, find roots using factorisation and formula methods, and solve real-world problems.",
        source_url="https://www.youtube.com/embed/ZCcCyb-15P8",
        source_platform="YouTube",
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
    db.add(item_math)

    # Item 2: Science (Human Respiration)
    item_science = ContentItem(
        title="Human Respiration Process Explained",
        description="Detailing aerobic vs anaerobic respiration, structure of alveoli, gaseous exchange, and how energy is released in cells.",
        source_url="https://www.youtube.com/embed/3nL2_O1wZ5Y",
        source_platform="YouTube",
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
    db.add(item_science)

    # Item 3: Coding (Python Functions)
    item_coding = ContentItem(
        title="Understanding Python Functions",
        description="A gentle intro to modular programming, def keyword, parameter scopes, arguments, return statements, and default values.",
        source_url="https://www.youtube.com/embed/9Os0o3wzS_I",
        source_platform="YouTube",
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
    db.add(item_coding)

    # Item 4: Science (Newton's Laws of Motion - Spaced Repetition Summary)
    item_physics = ContentItem(
        title="Spaced Revision: Newton's Laws of Motion",
        description="Brief summary of Newton's First, Second, and Third laws with interactive recall triggers.",
        source_url="https://www.physicsclassroom.com/class/newtlaws",
        source_platform="Physics Classroom",
        embed_code=None,
        type="reading",
        board="CBSE",
        grade_level=10,
        subject="Science",
        topic="Newton's Laws",
        difficulty="medium",
        duration_minutes=5,
        safety_score=100,
        edu_score=94,
        is_approved=True
    )
    db.add(item_physics)
    
    db.flush()

    # 6. Add Quizzes & Questions
    # Quiz 1: Math
    quiz_math = Quiz(content_item_id=item_math.id, title="Quadratic Equations Basic Check")
    db.add(quiz_math)
    db.flush()
    
    q_math_1 = Question(
        quiz_id=quiz_math.id,
        question_text="What is the standard form of a quadratic equation?",
        options=["ax + b = 0", "ax^2 + bx + c = 0", "ax^3 + bx^2 + cx + d = 0", "y = mx + c"],
        correct_answer="ax^2 + bx + c = 0",
        explanation="Standard quadratic form requires the highest degree of variable term to be squared (2).",
        difficulty="easy"
    )
    q_math_2 = Question(
        quiz_id=quiz_math.id,
        question_text="If the discriminant (b^2 - 4ac) is positive, what is the nature of the roots?",
        options=["Real and equal", "Real and distinct", "Complex / Imaginary", "No roots exist"],
        correct_answer="Real and distinct",
        explanation="A discriminant strictly greater than zero yields two distinct real numbers as solutions.",
        difficulty="medium"
    )
    q_math_3 = Question(
        quiz_id=quiz_math.id,
        question_text="Solve x^2 - 5x + 6 = 0.",
        options=["x = 1, 6", "x = 2, 3", "x = -2, -3", "x = -1, -6"],
        correct_answer="x = 2, 3",
        explanation="Factorising the expression gives (x - 2)(x - 3) = 0, so roots are x = 2 and x = 3.",
        difficulty="easy"
    )
    db.add_all([q_math_1, q_math_2, q_math_3])

    # Quiz 2: Science (Respiration)
    quiz_sci = Quiz(content_item_id=item_science.id, title="Respiration Dynamics Quiz")
    db.add(quiz_sci)
    db.flush()
    
    q_sci_1 = Question(
        quiz_id=quiz_sci.id,
        question_text="Which gas is released as a byproduct during aerobic respiration?",
        options=["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"],
        correct_answer="Carbon Dioxide",
        explanation="During cellular respiration, oxygen reacts with glucose to produce carbon dioxide, water, and ATP.",
        difficulty="easy"
    )
    q_sci_2 = Question(
        quiz_id=quiz_sci.id,
        question_text="Where does the first step of respiration (breakdown of glucose into pyruvate) occur?",
        options=["Mitochondria", "Cytoplasm", "Alveoli", "Ribosomes"],
        correct_answer="Cytoplasm",
        explanation="Glycolysis takes place in the cytoplasm, whereas further breakdown happens in the mitochondria.",
        difficulty="medium"
    )
    q_sci_3 = Question(
        quiz_id=quiz_sci.id,
        question_text="What is the energy currency of the cell produced during respiration?",
        options=["DNA", "RNA", "ATP", "Glucose"],
        correct_answer="ATP",
        explanation="ATP (Adenosine Triphosphate) stores and supplies cellular energy.",
        difficulty="easy"
    )
    db.add_all([q_sci_1, q_sci_2, q_sci_3])

    # Quiz 3: Coding (Python)
    quiz_code = Quiz(content_item_id=item_coding.id, title="Python Functions Core Check")
    db.add(quiz_code)
    db.flush()
    
    q_code_1 = Question(
        quiz_id=quiz_code.id,
        question_text="Which keyword is used to declare a function in Python?",
        options=["function", "fun", "def", "define"],
        correct_answer="def",
        explanation="Python uses the keyword 'def' to start a function block definition.",
        difficulty="easy"
    )
    q_code_2 = Question(
        quiz_id=quiz_code.id,
        question_text="What does a function return if there is no return statement inside it?",
        options=["0", "None", "False", "Undefined"],
        correct_answer="None",
        explanation="Python functions implicitly return the special object 'None' if execution finishes without a return instruction.",
        difficulty="medium"
    )
    q_code_3 = Question(
        quiz_id=quiz_code.id,
        question_text="What is the correct syntax to call a function named 'calculate' with argument '10'?",
        options=["calculate(10)", "calculate 10", "call calculate(10)", "calculate.run(10)"],
        correct_answer="calculate(10)",
        explanation="Functions in Python are invoked using parentheses directly after the function name.",
        difficulty="easy"
    )
    db.add_all([q_code_1, q_code_2, q_code_3])

    # Quiz 4: Spaced Revision Physics
    quiz_phys = Quiz(content_item_id=item_physics.id, title="Newton's Laws Recall Quiz")
    db.add(quiz_phys)
    db.flush()

    q_phys_1 = Question(
        quiz_id=quiz_phys.id,
        question_text="Which law states that an object will remain at rest unless acted upon by an external force?",
        options=["First Law", "Second Law", "Third Law", "Law of Gravitation"],
        correct_answer="First Law",
        explanation="Newton's First Law (Law of Inertia) states that state changes require an external unbalanced force.",
        difficulty="easy"
    )
    q_phys_2 = Question(
        quiz_id=quiz_phys.id,
        question_text="What is the formula representing Newton's Second Law?",
        options=["F = m/a", "F = ma", "F = mv", "F = m^2a"],
        correct_answer="F = ma",
        explanation="Force equals Mass times Acceleration (F = ma) represents the Second Law of Motion.",
        difficulty="easy"
    )
    db.add_all([q_phys_1, q_phys_2])

    db.commit()
    print("Database seeded successfully with default schools, students, parents, content, and quizzes.")
    db.close()

if __name__ == "__main__":
    seed_database()
