import datetime
import uuid
from sqlalchemy import (
    Column, String, Integer, BigInteger, Boolean, Date, DateTime, Numeric, JSON,
    ForeignKey, Table, Text, UniqueConstraint, Index, CheckConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
    Vector = None

def generate_uuid():
    return str(uuid.uuid4())

# Parent-Student Link Table
parent_student_links = Table(
    "parent_student_links",
    Base.metadata,
    Column("parent_user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("student_user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("relationship_type", String, default="guardian"), # 'parent', 'guardian', 'tutor'
    Column("is_verified", Boolean, default=False),
    Column("verified_at", DateTime, nullable=True),
    Column("revoked_at", DateTime, nullable=True),
    Column("verification_method", String, default="email_otp") # 'email_otp', 'school_admin_attestation'
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
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    classes = relationship("SchoolClass", back_populates="school", cascade="all, delete-orphan")
    users = relationship("User", back_populates="school")

class SchoolClass(Base):
    __tablename__ = "school_classes"
    __table_args__ = (
        UniqueConstraint("school_id", "grade_level", "section_name", "academic_year", name="uq_school_class"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    school_id = Column(String, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    grade_level = Column(Integer, nullable=False) # e.g. 10
    section_name = Column(String, nullable=False) # e.g. "A"
    academic_year = Column(String, nullable=False) # e.g. "2026-2027"
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    school = relationship("School", back_populates="classes")
    students = relationship("StudentProfile", back_populates="school_class")

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    role = Column(String, nullable=False) # 'student', 'parent', 'teacher', 'school_admin', 'super_admin'
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    guardian_verified = Column(Boolean, default=False)
    identity_verified = Column(Boolean, default=False) # Separated from consent
    account_status = Column(String, default="ACTIVE") # ACTIVE, SUSPENDED, DEACTIVATED
    token_version = Column(Integer, default=1, nullable=False) # Incremented on password reset to invalidate active JWTs
    password_changed_at = Column(DateTime, nullable=True) # Explicit timestamp of last credential reset
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    school_id = Column(String, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    school = relationship("School", back_populates="users")

    student_profile = relationship("StudentProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
    quiz_attempts = relationship("QuizAttempt", back_populates="student", cascade="all, delete-orphan")
    progress_logs = relationship("StudentProgress", back_populates="student", cascade="all, delete-orphan")
    spaced_schedules = relationship("SpacedRepetitionSchedule", back_populates="student", cascade="all, delete-orphan")
    topic_masteries = relationship("TopicMastery", back_populates="student", cascade="all, delete-orphan")

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
    grade_level = Column(Integer, nullable=True, default=10) # Explicit student grade level
    board = Column(String, default="CBSE") # 'CBSE', 'ICSE', 'State_Board', 'IB', 'IGCSE'
    date_of_birth = Column(Date, nullable=True) # Nullable for incomplete onboarding (e.g. Google sign-in)
    onboarding_status = Column(String, default="PENDING") # 'PENDING', 'COMPLETED'
    parental_consent_status = Column(String, default="PENDING") # 'PENDING', 'GRANTED', 'REVOKED', 'EXEMPT_ADULT'
    learning_access_status = Column(String, default="ACTIVE") # 'ACTIVE', 'RESTRICTED'
    xp_score = Column(Integer, default=0)
    streak_count = Column(Integer, default=0)
    last_active_date = Column(Date, nullable=True)
    interests = Column(JSON, default=list) # Store list of strings, e.g. ["coding", "space"]
    learning_preference = Column(JSON, default=list) # Store list of strings, e.g. ["video", "reading"]
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    user = relationship("User", back_populates="student_profile")
    school_class = relationship("SchoolClass", back_populates="students")

class ContentItem(Base):
    __tablename__ = "content_items"
    __table_args__ = (
        Index("ix_content_items_board_grade_approved", "board", "grade_level", "is_approved"),
    )
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
    safety_labels = Column(JSON, default=dict) # e.g. {"toxicity": 0.0, "verdict": "ALLOW"}
    embedding = Column(Vector(384) if (HAS_PGVECTOR and Vector is not None) else JSON, nullable=True) # Semantic dense vector embedding
    tags = Column(JSON, default=list) # e.g. ["python", "loops", "coding"]
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    is_approved = Column(Boolean, default=False)
    moderation_status = Column(String, default="APPROVED")  # 'DISCOVERED', 'QUARANTINED', 'AUTOMATED_SCREENING', 'APPROVED', 'NEEDS_HUMAN_REVIEW', 'REJECTED'
    transcript_text = Column(Text, nullable=True)
    content_hash = Column(String, nullable=True)
    transcript_hash = Column(String, nullable=True)
    policy_version = Column(String, default="2026.2")
    source_id = Column(String, nullable=True)
    provenance_metadata = Column(JSON, default=dict)
    checked_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    school_id = Column(String, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    quizzes = relationship("Quiz", back_populates="content_item", cascade="all, delete-orphan")
    progress_logs = relationship("StudentProgress", back_populates="content_item", cascade="all, delete-orphan")
    interactions = relationship("UserInteraction", back_populates="content_item", cascade="all, delete-orphan")

class UserInteraction(Base):
    __tablename__ = "user_interactions"
    __table_args__ = (
        Index("ix_user_interactions_user_content", "user_id", "content_item_id"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_item_id = Column(String, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False)
    interaction_type = Column(String, nullable=False) # 'view', 'click', 'watch_time', 'completed', 'quiz_completed', 'bookmark', 'like', 'skip'
    weight = Column(Numeric(4, 2), default=1.0) # +5 for completion, +4 for bookmark, -2 for skip, etc.
    dwell_time_seconds = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    user = relationship("User")
    content_item = relationship("ContentItem", back_populates="interactions")

class StudentProgress(Base):
    __tablename__ = "student_progress"
    __table_args__ = (
        UniqueConstraint("student_user_id", "content_item_id", name="uq_student_content_progress"),
        CheckConstraint("progress_percentage >= 0 AND progress_percentage <= 100", name="ck_student_progress_percentage"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_item_id = Column(String, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False)
    progress_percentage = Column(Integer, default=0) # 0 to 100
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    student = relationship("User", back_populates="progress_logs")
    content_item = relationship("ContentItem", back_populates="progress_logs")

class Quiz(Base):
    __tablename__ = "quizzes"
    id = Column(String, primary_key=True, default=generate_uuid)
    content_item_id = Column(String, ForeignKey("content_items.id", ondelete="SET NULL"), nullable=True)
    school_id = Column(String, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    content_item = relationship("ContentItem", back_populates="quizzes")
    school = relationship("School")
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
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    quiz = relationship("Quiz", back_populates="questions")

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    __table_args__ = (
        UniqueConstraint("student_user_id", "quiz_id", "attempt_number", name="uq_student_quiz_attempt"),
        CheckConstraint("score >= 0 AND max_score > 0 AND accuracy_percentage >= 0 AND accuracy_percentage <= 100", name="ck_quiz_attempt_scores"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    quiz_id = Column(String, ForeignKey("quizzes.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt_number = Column(Integer, default=1, index=True)
    score = Column(Integer, nullable=False)
    max_score = Column(Integer, nullable=False)
    accuracy_percentage = Column(Numeric(5, 2), nullable=False)
    xp_awarded = Column(Integer, default=0)
    completed_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    student = relationship("User", back_populates="quiz_attempts")
    quiz = relationship("Quiz", back_populates="attempts")

class SpacedRepetitionSchedule(Base):
    __tablename__ = "spaced_repetition_schedules"
    __table_args__ = (
        UniqueConstraint("student_user_id", "subject", "topic", name="uq_student_topic_schedule"),
        CheckConstraint("easiness_factor >= 1.30 AND interval_days >= 0", name="ck_sm2_easiness_factor"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    interval_days = Column(Integer, default=1)
    repetition_number = Column(Integer, default=0)
    easiness_factor = Column(Numeric(3, 2), default=2.50)
    next_review_date = Column(Date, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    student = relationship("User", back_populates="spaced_schedules")

class Flashcard(Base):
    __tablename__ = "flashcards"
    id = Column(String, primary_key=True, default=generate_uuid)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    front_text = Column(String, nullable=False)
    back_text = Column(String, nullable=False)
    hint = Column(String, nullable=True)
    grade_level = Column(Integer, default=10)
    board = Column(String, default="CBSE")
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class Badge(Base):
    __tablename__ = "badges"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False) # e.g. "streak_7", "quiz_100", "math_master"
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    icon = Column(String, nullable=False) # FontAwesome icon class e.g. "fa-fire"
    category = Column(String, default="achievement")
    xp_bonus = Column(Integer, default=50)

class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = (
        UniqueConstraint("user_id", "badge_id", name="uq_user_badge"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_id = Column(String, ForeignKey("badges.id", ondelete="CASCADE"), nullable=False)
    unlocked_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    badge = relationship("Badge")
    user = relationship("User")

class ClassAssignment(Base):
    __tablename__ = "class_assignments"
    __table_args__ = (
        Index("ix_class_assignments_teacher_class", "teacher_user_id", "class_id"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    teacher_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    class_id = Column(String, ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False)
    content_item_id = Column(String, ForeignKey("content_items.id", ondelete="SET NULL"), nullable=True)
    quiz_id = Column(String, ForeignKey("quizzes.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=False)
    instructions = Column(String, nullable=True)
    due_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    teacher = relationship("User")
    school_class = relationship("SchoolClass")
    content_item = relationship("ContentItem")
    quiz = relationship("Quiz")

class TopicMastery(Base):
    """
    Topic-level student mastery index tracking diagnostic comprehension,
    confidence score, assessment history, and learning trajectory trend.
    Forms the central learning intelligence layer linking quizzes, SM-2, and recommendations.
    """
    __tablename__ = "topic_masteries"
    __table_args__ = (
        UniqueConstraint("student_user_id", "subject", "topic", name="uq_student_topic_mastery"),
        Index("ix_topic_masteries_student_subject", "student_user_id", "subject"),
        CheckConstraint("mastery_score >= 0 AND mastery_score <= 100", name="ck_topic_mastery_score"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    board = Column(String, default="CBSE")
    grade_level = Column(Integer, default=10)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    mastery_score = Column(Numeric(5, 2), default=0.0) # 0.00 to 100.00 (%)
    confidence = Column(Numeric(4, 2), default=0.5) # 0.00 to 1.00
    attempt_count = Column(Integer, default=0)
    trend = Column(String, default="stable") # 'improving', 'stable', 'declining'
    last_assessed_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))

    student = relationship("User", back_populates="topic_masteries")

class CurriculumChunk(Base):
    """
    Structured database-backed curriculum knowledge chunk for RAG and semantic vector search.
    Supports pgvector embeddings, section provenance, and PostgreSQL database storage.
    """
    __tablename__ = "curriculum_chunks"
    __table_args__ = (
        Index("ix_curriculum_chunks_subject_topic", "subject", "topic", "grade_level"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    source_id = Column(String, ForeignKey("content_items.id", ondelete="SET NULL"), nullable=True)
    source_url = Column(String, nullable=True)
    source_doc = Column(String, nullable=True) # e.g. "NCERT Class 10 Science - Light"
    board = Column(String, default="CBSE") # 'CBSE', 'ICSE', 'State_Board'
    grade_level = Column(Integer, default=10)
    subject = Column(String, nullable=False) # 'Mathematics', 'Science', 'Computer Science', 'Space Science'
    topic = Column(String, nullable=False)
    chapter = Column(String, nullable=True)
    section = Column(String, nullable=False)
    chunk_index = Column(Integer, default=0)
    curriculum_code = Column(String, index=True, nullable=True) # e.g. "CBSE-G10-MATH-QUADRA"
    chunk_text = Column(Text, nullable=False)
    embedding = Column(Vector(384) if (HAS_PGVECTOR and Vector is not None) else JSON, nullable=True) # 384-dimensional dense semantic vector
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class IngestedSource(Base):
    """
    Staging table for the automated Content Intelligence Ingestion Pipeline.
    Supports 11-stage finite state machine and failure recovery.
    """
    __tablename__ = "ingested_sources"
    id = Column(String, primary_key=True, default=generate_uuid)
    source_url = Column(String, nullable=False)
    url_hash = Column(String, unique=True, index=True, nullable=False) # SHA-256 canonical digest
    source_platform = Column(String, nullable=False) # 'youtube', 'khan_academy', 'ncert_oer', 'phet', 'pdf', 'html'
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True) # Extracted transcript or OER text
    subject = Column(String, nullable=True)
    topic = Column(String, nullable=True)
    chapter = Column(String, nullable=True)
    grade_level = Column(Integer, default=10)
    board = Column(String, default="CBSE")
    curriculum_code = Column(String, nullable=True)
    status = Column(String, default="DISCOVERED") # DISCOVERED, FETCHING, EXTRACTED, NORMALIZED, CURRICULUM_MAPPED, SAFETY_CHECKED, CHUNKED, EMBEDDED, PENDING_REVIEW, APPROVED, PUBLISHED, FAILED
    error_code = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    pipeline_version = Column(String, default="2.0")
    safety_audit = Column(JSON, nullable=True)
    edu_score = Column(Integer, default=80)
    submitted_by = Column(String, nullable=True)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

class ParentalConsentLog(Base):
    """
    Verifiable Parental Consent & Child Privacy Audit Log.
    Complies with COPPA, GDPR-K, and India DPDP Act 2023 provisions for minors under 18.
    """
    __tablename__ = "parental_consent_logs"
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    parent_email = Column(String, nullable=False)
    consent_status = Column(String, default="granted") # 'granted', 'revoked', 'pending_verification'
    verification_method = Column(String, default="email_verification") # 'email_verification', 'school_admin_attestation', 'guardian_portal'
    verification_token = Column(String, nullable=True)
    ip_hash = Column(String, nullable=True)
    consent_scope = Column(JSON, default=list) # e.g. ["curriculum_access", "ai_socratic_tutor", "analytics_tracking"]
    granted_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    revoked_at = Column(DateTime, nullable=True)

    student = relationship("User", foreign_keys=[student_user_id])
    parent = relationship("User", foreign_keys=[parent_user_id])

class ContentReport(Base):
    """
    Student and parent content reporting feedback loop for pedagogical and safety moderation.
    Feeds directly into educator and administrative moderation queues.
    """
    __tablename__ = "content_reports"
    id = Column(String, primary_key=True, default=generate_uuid)
    reporter_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_item_id = Column(String, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False)
    reason = Column(String, nullable=False) # 'Unsafe', 'Incorrect', 'Not age appropriate', 'Not educational', 'Broken', 'Other'
    details = Column(Text, nullable=True)
    status = Column(String, default="pending_review") # 'pending_review', 'resolved', 'dismissed'
    action_taken = Column(String, nullable=True)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    reporter = relationship("User")
    content_item = relationship("ContentItem")

class PendingGuardianInvitation(Base):
    """
    Staging invitation record for legal guardian accounts created during student registration.
    Guardian receives an activation email with OTP to establish their own credentials and verify consent.
    """
    __tablename__ = "pending_guardian_invitations"
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    guardian_email = Column(String, nullable=False, index=True)
    invitation_token = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, default="pending") # 'pending', 'accepted', 'expired'
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    student = relationship("User")


class StaffInvitation(Base):
    """
    Authoritative database record for staff (teacher, school_admin) invitations.
    Stores SHA-256 hash of the invitation token, supporting explicit lifecycle states:
    PENDING -> ACCEPTED, REVOKED, or EXPIRED.
    """
    __tablename__ = "staff_invitations"
    __table_args__ = (
        Index("ix_staff_invitations_school_status", "school_id", "status"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(String, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)
    role = Column(String, default="teacher") # 'teacher', 'school_admin'
    token_hash = Column(String, unique=True, index=True, nullable=False) # SHA-256 hex digest
    status = Column(String, default="PENDING") # 'PENDING', 'ACCEPTED', 'REVOKED', 'EXPIRED'
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    accepted_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_by = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    school = relationship("School", foreign_keys=[school_id])
    creator = relationship("User", foreign_keys=[created_by])


class LearningEvent(Base):
    """
    Authoritative server-side learning event log for tracking verified student engagement.
    Replaces unverified client completion submissions with audited event streams.
    """
    __tablename__ = "learning_events"
    __table_args__ = (
        Index("ix_learning_events_student_content", "student_user_id", "content_item_id"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content_item_id = Column(String, ForeignKey("content_items.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String, nullable=False)  # 'heartbeat', 'progress_checkpoint', 'completion_verified', 'quiz_submission'
    progress_percentage = Column(Integer, default=0)
    verified_seconds = Column(Integer, default=0)
    heartbeat_count = Column(Integer, default=0)
    client_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    student = relationship("User")
    content_item = relationship("ContentItem")


class RewardLedger(Base):
    """
    Immutable transaction ledger for XP and gamification disbursements.
    Guarantees idempotency via unique_reward_key, preventing duplicate awards and race conditions.
    """
    __tablename__ = "reward_ledgers"
    __table_args__ = (
        UniqueConstraint("unique_reward_key", name="uq_reward_unique_key"),
        Index("ix_reward_ledgers_student", "student_user_id"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_id = Column(String, nullable=True)
    reward_type = Column(String, nullable=False)  # 'CONTENT_COMPLETION_XP', 'QUIZ_MASTERY_XP', 'STREAK_BONUS_XP'
    xp_amount = Column(Integer, nullable=False)
    unique_reward_key = Column(String, nullable=False, unique=True, index=True)  # e.g. "xp:completion:{student_id}:{content_id}"
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    student = relationship("User")


class ConceptNode(Base):
    """
    Represents a discrete pedagogical concept in the K-12 curriculum knowledge graph.
    Supports curriculum versioning and temporal validity.
    """
    __tablename__ = "concept_nodes"
    id = Column(String, primary_key=True, default=generate_uuid)
    code = Column(String, unique=True, index=True, nullable=False)  # e.g. "MATH_G10_QUAD_DISCRIMINANT"
    subject = Column(String, nullable=False, index=True)
    topic = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    grade_level = Column(Integer, nullable=False)
    board = Column(String, default="CBSE")
    curriculum_version = Column(String, default="2026.1", index=True)
    effective_from = Column(Date, nullable=True)
    effective_until = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class PrerequisiteEdge(Base):
    """
    Directed prerequisite relationship between concepts: concept_id requires prerequisite_concept_id.
    Tracks provenance source authority and confidence score.
    """
    __tablename__ = "prerequisite_edges"
    __table_args__ = (
        UniqueConstraint("concept_id", "prerequisite_concept_id", name="uq_prerequisite_edge"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    concept_id = Column(String, ForeignKey("concept_nodes.id", ondelete="CASCADE"), nullable=False)
    prerequisite_concept_id = Column(String, ForeignKey("concept_nodes.id", ondelete="CASCADE"), nullable=False)
    weight = Column(Numeric(3, 2), default=1.0)
    source = Column(String, default="CURRICULUM_OFFICIAL")  # 'CURRICULUM_OFFICIAL', 'TEACHER_AUTHORED', 'AI_INFERRED'
    confidence = Column(Numeric(3, 2), default=0.95)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    concept = relationship("ConceptNode", foreign_keys=[concept_id])
    prerequisite = relationship("ConceptNode", foreign_keys=[prerequisite_concept_id])


class MisconceptionLog(Base):
    """
    Tracks persistent student cognitive misconceptions diagnosed during Socratic tutoring or quiz attempts.
    """
    __tablename__ = "misconception_logs"
    __table_args__ = (
        Index("ix_misconceptions_student_concept", "student_user_id", "concept_code"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    concept_code = Column(String, nullable=True)
    pattern = Column(String, nullable=False)  # e.g. "confuses_acceleration_with_velocity"
    confidence = Column(Numeric(3, 2), default=0.85)
    first_seen_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    student = relationship("User")


class AuditEvent(Base):
    """
    Immutable audit log tracking all sensitive resource access, authentication events,
    and cross-tenant authorization checks.
    Employs cryptographic hash-chaining (previous_event_hash) to make database alterations detectable.
    """
    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_actor", "actor_id", "timestamp"),
        Index("ix_audit_events_resource", "resource_type", "resource_id"),
        Index("ix_audit_events_school", "school_id", "timestamp"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    sequence_number = Column(BigInteger, unique=True, index=True, nullable=False, default=1)
    previous_event_hash = Column(String, nullable=True)
    event_hash = Column(String, nullable=False, index=True)
    actor_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_role = Column(String, nullable=True)
    school_id = Column(String, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)  # 'VIEW_CHILD_PROFILE', 'ACCESS_STUDENT_DATA', 'SECURITY_DENIED', 'PASSWORD_RESET'
    resource_type = Column(String, nullable=False)  # 'student_profile', 'content_item', 'quiz', 'school_class'
    resource_id = Column(String, nullable=True)
    status = Column(String, nullable=False, default="SUCCESS")  # 'SUCCESS', 'DENIED', 'ERROR'
    reason = Column(Text, nullable=True)
    ip_hash = Column(String, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)

    actor = relationship("User", foreign_keys=[actor_id])
    school = relationship("School", foreign_keys=[school_id])


class ConsentRecord(Base):
    """
    Enforceable database consent registry tracking verified guardian and statutory consent decisions
    per processing purpose under the DPDP Act 2023.
    """
    __tablename__ = "consent_records"
    __table_args__ = (
        UniqueConstraint("student_user_id", "processing_purpose", name="uq_student_consent_purpose"),
        Index("ix_consent_records_student_status", "student_user_id", "status"),
    )
    id = Column(String, primary_key=True, default=generate_uuid)
    student_user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    guardian_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    processing_purpose = Column(String, nullable=False)  # 'ai_socratic_tutor', 'personalized_recommendations', etc.
    consent_scope = Column(String, nullable=False)
    status = Column(String, default="ACTIVE")  # 'ACTIVE', 'REVOKED', 'EXPIRED'
    policy_version = Column(String, default="2026.2-DPDP")
    verification_method = Column(String, default="GUARDIAN_EMAIL_OTP")
    granted_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)

    student = relationship("User", foreign_keys=[student_user_id])
    guardian = relationship("User", foreign_keys=[guardian_user_id])
