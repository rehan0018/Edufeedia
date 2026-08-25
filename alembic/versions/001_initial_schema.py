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
    # 1. PostgreSQL Extension (if postgres dialect)
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Schools Table
    op.create_table(
        'schools',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), unique=True, index=True),
        sa.Column('address', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )

    # 3. School Classes Table
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

    # 4. Users Table
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

    # 5. Parent-Student Links
    op.create_table(
        'parent_student_links',
        sa.Column('parent_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('student_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('is_verified', sa.Boolean(), default=False)
    )

    # 6. Teacher-Class Links
    op.create_table(
        'teacher_classes',
        sa.Column('teacher_user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('class_id', sa.String(), sa.ForeignKey('school_classes.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('subject', sa.String(), primary_key=True)
    )

    # 7. Student Profiles
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

    # 8. Content Items
    embedding_col = Vector(384) if (HAS_PGVECTOR and Vector is not None) else sa.JSON()
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

    # 9. Spaced Repetition Schedules
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

    # 10. Content Reports
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

    # 11. Pending Guardian Invitations
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
    op.drop_table('spaced_repetition_schedules')
    op.drop_table('content_items')
    op.drop_table('student_profiles')
    op.drop_table('teacher_classes')
    op.drop_table('parent_student_links')
    op.drop_table('users')
    op.drop_table('school_classes')
    op.drop_table('schools')
