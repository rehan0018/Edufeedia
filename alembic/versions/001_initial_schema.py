"""initial_schema_baseline

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-20 17:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
    Vector = None

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    conn = op.get_bind()
    is_postgres = (conn.dialect.name == "postgresql")
    if is_postgres:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    embedding_col = Vector(384) if (HAS_PGVECTOR and Vector is not None and is_postgres) else sa.JSON()

    # 1. Schools Table
    op.create_table(
        'schools',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), unique=True, index=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 2. School Classes Table
    op.create_table(
        'school_classes',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('school_id', sa.String(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('grade_level', sa.Integer(), nullable=False),
        sa.Column('section_name', sa.String(), nullable=False),
        sa.Column('academic_year', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('school_id', 'grade_level', 'section_name', 'academic_year', name='uq_school_class')
    )

    # 3. Users Table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('email', sa.String(), unique=True, index=True, nullable=False),
        sa.Column('password_hash', sa.String(), nullable=True),
        sa.Column('google_id', sa.String(), unique=True, index=True, nullable=True),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('first_name', sa.String(), nullable=False),
        sa.Column('last_name', sa.String(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('identity_verified', sa.Boolean(), default=False),
        sa.Column('account_status', sa.String(), default='ACTIVE'),
        sa.Column('school_id', sa.String(), sa.ForeignKey('schools.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 4. Parent-Student Links
    op.create_table(
        'parent_student_links',
        sa.Column('parent_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('student_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('is_verified', sa.Boolean(), default=False)
    )

    # 5. Teacher-Class Links
    op.create_table(
        'teacher_classes',
        sa.Column('teacher_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('class_id', sa.String(), sa.ForeignKey('school_classes.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('subject', sa.String(), primary_key=True)
    )

    # 6. Student Profiles
    op.create_table(
        'student_profiles',
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('school_id', sa.String(), sa.ForeignKey('schools.id', ondelete='SET NULL'), nullable=True),
        sa.Column('class_id', sa.String(), sa.ForeignKey('school_classes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('grade_level', sa.Integer(), nullable=True, default=10),
        sa.Column('board', sa.String(), default='CBSE'),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('onboarding_status', sa.String(), default='PENDING'),
        sa.Column('parental_consent_status', sa.String(), default='PENDING'),
        sa.Column('learning_access_status', sa.String(), default='ACTIVE'),
        sa.Column('xp_score', sa.Integer(), default=0),
        sa.Column('streak_count', sa.Integer(), default=0),
        sa.Column('last_active_date', sa.Date(), nullable=True),
        sa.Column('interests', sa.JSON(), default=list),
        sa.Column('learning_preference', sa.JSON(), default=list),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 7. Content Items
    op.create_table(
        'content_items',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('source_url', sa.String(), unique=True, index=True, nullable=False),
        sa.Column('source_platform', sa.String(), nullable=False),
        sa.Column('embed_code', sa.String(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('board', sa.String(), nullable=False),
        sa.Column('grade_level', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('difficulty', sa.String(), default='medium'),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('safety_score', sa.Integer(), default=100),
        sa.Column('edu_score', sa.Integer(), default=100),
        sa.Column('safety_labels', sa.JSON(), default=dict),
        sa.Column('embedding', embedding_col, nullable=True),
        sa.Column('tags', sa.JSON(), default=list),
        sa.Column('view_count', sa.Integer(), default=0),
        sa.Column('like_count', sa.Integer(), default=0),
        sa.Column('is_approved', sa.Boolean(), default=False),
        sa.Column('school_id', sa.String(), sa.ForeignKey('schools.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 8. User Interactions
    op.create_table(
        'user_interactions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content_item_id', sa.String(), sa.ForeignKey('content_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('interaction_type', sa.String(), nullable=False),
        sa.Column('weight', sa.Numeric(3, 2), default=1.00),
        sa.Column('dwell_time_seconds', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 9. Student Progress
    op.create_table(
        'student_progress',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('student_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content_item_id', sa.String(), sa.ForeignKey('content_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('progress_percentage', sa.Integer(), default=0),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('student_user_id', 'content_item_id', name='uq_student_content_progress')
    )

    # 10. Quizzes
    op.create_table(
        'quizzes',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('content_item_id', sa.String(), sa.ForeignKey('content_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('school_id', sa.String(), sa.ForeignKey('schools.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 11. Questions
    op.create_table(
        'questions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('quiz_id', sa.String(), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_text', sa.String(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False),
        sa.Column('correct_answer', sa.String(), nullable=False),
        sa.Column('explanation', sa.String(), nullable=True),
        sa.Column('difficulty', sa.String(), default='medium')
    )

    # 12. Quiz Attempts
    op.create_table(
        'quiz_attempts',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('student_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quiz_id', sa.String(), sa.ForeignKey('quizzes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('max_score', sa.Integer(), nullable=False),
        sa.Column('accuracy_percentage', sa.Numeric(5, 2), nullable=False),
        sa.Column('attempt_details', sa.JSON(), default=list),
        sa.Column('completed_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 13. Spaced Repetition Schedules
    op.create_table(
        'spaced_repetition_schedules',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('student_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('interval_days', sa.Integer(), default=1),
        sa.Column('repetition_number', sa.Integer(), default=0),
        sa.Column('easiness_factor', sa.Numeric(3, 2), default=2.50),
        sa.Column('next_review_date', sa.Date(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('student_user_id', 'subject', 'topic', name='uq_student_topic_schedule')
    )

    # 14. Flashcards
    op.create_table(
        'flashcards',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('front_text', sa.String(), nullable=False),
        sa.Column('back_text', sa.String(), nullable=False),
        sa.Column('hint', sa.String(), nullable=True),
        sa.Column('grade_level', sa.Integer(), default=10),
        sa.Column('board', sa.String(), default='CBSE'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 15. Badges
    op.create_table(
        'badges',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('code', sa.String(), unique=True, index=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('icon', sa.String(), nullable=False),
        sa.Column('xp_bonus', sa.Integer(), default=50),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 16. User Badges
    op.create_table(
        'user_badges',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('badge_id', sa.String(), sa.ForeignKey('badges.id', ondelete='CASCADE'), nullable=False),
        sa.Column('unlocked_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('user_id', 'badge_id', name='uq_user_badge')
    )

    # 17. Class Assignments
    op.create_table(
        'class_assignments',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('class_id', sa.String(), sa.ForeignKey('school_classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content_item_id', sa.String(), sa.ForeignKey('content_items.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 18. Curriculum Chunks
    op.create_table(
        'curriculum_chunks',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('grade_level', sa.Integer(), nullable=False),
        sa.Column('section', sa.String(), nullable=False),
        sa.Column('chunk_text', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), default=0),
        sa.Column('source_doc', sa.String(), nullable=True),
        sa.Column('embedding', embedding_col, nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 19. Ingested Sources
    op.create_table(
        'ingested_sources',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('source_url', sa.String(), unique=True, index=True, nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('status', sa.String(), default='pending'),
        sa.Column('safety_score', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 20. Parental Consent Logs
    op.create_table(
        'parental_consent_logs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('student_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('parent_email', sa.String(), nullable=False),
        sa.Column('consent_status', sa.String(), nullable=False),
        sa.Column('verification_method', sa.String(), default='email_otp'),
        sa.Column('consent_scope', sa.JSON(), default=list),
        sa.Column('granted_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('revoked_at', sa.DateTime(), nullable=True)
    )

    # 21. Content Reports
    op.create_table(
        'content_reports',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('reporter_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('content_item_id', sa.String(), sa.ForeignKey('content_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), default='pending_review'),
        sa.Column('action_taken', sa.String(), nullable=True),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 22. Pending Guardian Invitations
    op.create_table(
        'pending_guardian_invitations',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('student_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('guardian_email', sa.String(), index=True, nullable=False),
        sa.Column('invitation_token', sa.String(), unique=True, index=True, nullable=False),
        sa.Column('status', sa.String(), default='pending'),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

def downgrade() -> None:
    op.drop_table('pending_guardian_invitations')
    op.drop_table('content_reports')
    op.drop_table('parental_consent_logs')
    op.drop_table('ingested_sources')
    op.drop_table('curriculum_chunks')
    op.drop_table('class_assignments')
    op.drop_table('user_badges')
    op.drop_table('badges')
    op.drop_table('flashcards')
    op.drop_table('spaced_repetition_schedules')
    op.drop_table('quiz_attempts')
    op.drop_table('questions')
    op.drop_table('quizzes')
    op.drop_table('student_progress')
    op.drop_table('user_interactions')
    op.drop_table('content_items')
    op.drop_table('student_profiles')
    op.drop_table('teacher_classes')
    op.drop_table('parent_student_links')
    op.drop_table('users')
    op.drop_table('school_classes')
    op.drop_table('schools')
