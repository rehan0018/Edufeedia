import datetime
import uuid
from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, Numeric, JSON, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

# Parent-Student Link Table
parent_student_links = Table(
    "parent_student_links",
    Base.metadata,
    Column("parent_user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("student_user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("is_verified", Boolean, default=False)
)

# Teacher-Class Link Table
teacher_classes = Table(
    "teacher_classes",
    Base.metadata,
    Column("teacher_user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("class_id", String, ForeignKey("school_classes.id", ondelete="CASCADE"), primary_key=True),
    Column("subject", String, primary_key=True)
)

class School(Base):
    __tablename__ = "schools"
    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, index=True)
    address = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    classes = relationship("SchoolClass", back_populates="school", cascade="all, delete-orphan")
    users = relationship("User", back_populates="school")

class SchoolClass(Base):
    __tablename__ = "school_classes"
    id = Column(String, primary_key=True, default=generate_uuid)
    school_id = Column(String, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    grade_level = Column(Integer, nullable=False) # e.g. 10
    section_name = Column(String, nullable=False) # e.g. "A"
    academic_year = Column(String, nullable=False) # e.g. "2026-2027"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    school = relationship("School", back_populates="classes")
    students = relationship("StudentProfile", back_populates="school_class")

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False) # 'student', 'parent', 'teacher', 'school_admin', 'super_admin'
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    school_id = Column(String, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    school = relationship("School", back_populates="users")

    student_profile = relationship("StudentProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="student", cascade="all, delete-orphan")
    progress_logs = relationship("StudentProgress", back_populates="student", cascade="all, delete-orphan")
    spaced_schedules = relationship("SpacedRepetitionSchedule", back_populates="student", cascade="all, delete-orphan")

    # Relationships for parents
    students_linked = relationship(
        "User",
        secondary=parent_student_links,
        primaryjoin="User.id==parent_student_links.c.parent_user_id",
        secondaryjoin="User.id==parent_student_links.c.student_user_id",
        backref="parents_linked"
    )

class StudentProfile(Base):
    __tablename__ = "student_profiles"
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    school_id = Column(String, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    class_id = Column(String, ForeignKey("school_classes.id", ondelete="SET NULL"), nullable=True)
    board = Column(String, default="CBSE") # 'CBSE', 'ICSE', 'State_Board', 'IB', 'IGCSE'
    date_of_birth = Column(Date, nullable=False)
    xp_score = Column(Integer, default=0)
    streak_count = Column(Integer, default=0)
    last_active_date = Column(Date, nullable=True)
    interests = Column(JSON, default=list) # Store list of strings, e.g. ["coding", "space"]
    learning_preference = Column(JSON, default=list) # Store list of strings, e.g. ["video", "reading"]
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="student_profile")
    school_class = relationship("SchoolClass", back_populates="students")

class ContentItem(Base):
    __tablename__ = "content_items"
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String, nullable=False)
    description = Column(String)
    source_url = Column(String, unique=True, index=True, nullable=False)
    source_platform = Column(String, nullable=False) # 'YouTube', 'NCERT', 'OER'
    embed_code = Column(String, nullable=True)
    type = Column(String, nullable=False) # 'video', 'reading', 'interactive'
    board = Column(String, nullable=False) # 'CBSE', 'ICSE', etc.
    grade_level = Column(Integer, nullable=False)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    difficulty = Column(String, default="medium") # 'easy', 'medium', 'hard'
    duration_minutes = Column(Integer, nullable=False)
    safety_score = Column(Integer, default=100)
    edu_score = Column(Integer, default=100)
    is_approved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    quizzes = relationship("Quiz", back_populates="content_item", cascade="all, delete-orphan")
    progress_logs = relationship("StudentProgress", back_populates="content_item", cascade="all, delete-orphan")

class StudentProgress(Base):
    __tablename__ = "student_progress"
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_item_id = Column(String, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False)
    progress_percentage = Column(Integer, default=0) # 0 to 100
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    student = relationship("User", back_populates="progress_logs")
    content_item = relationship("ContentItem", back_populates="progress_logs")

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(String, primary_key=True, default=generate_uuid)
    content_item_id = Column(String, ForeignKey("content_items.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    content_item = relationship("ContentItem", back_populates="quizzes")
    questions = relationship("Question", back_populates="quiz", cascade="all, delete-orphan")
    attempts = relationship("QuizAttempt", back_populates="quiz", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    id = Column(String, primary_key=True, default=generate_uuid)
    quiz_id = Column(String, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(String, nullable=False)
    question_type = Column(String, default="multiple_choice")
    options = Column(JSON, nullable=True) # For MCQ: ["Option A", "Option B", ...]
    correct_answer = Column(String, nullable=False)
    explanation = Column(String, nullable=True)
    difficulty = Column(String, default="medium")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    quiz = relationship("Quiz", back_populates="questions")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    quiz_id = Column(String, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False)
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    accuracy_percentage = Column(Numeric(5, 2), nullable=False)
    completed_at = Column(DateTime, default=datetime.datetime.utcnow)

    student = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")

class SpacedRepetitionSchedule(Base):
    __tablename__ = "spaced_repetition_schedules"
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    interval_days = Column(Integer, default=1)
    repetition_number = Column(Integer, default=0)
    easiness_factor = Column(Numeric(3, 2), default=2.50)
    next_review_date = Column(Date, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    student = relationship("User", back_populates="spaced_schedules")
