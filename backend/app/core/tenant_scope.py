"""
Reusable Tenant Scope Engine.
Applies strict, multi-tenant relational isolation filters across SQLAlchemy queries.
Guarantees that school-level administrators and educators cannot access foreign school records.
"""

from typing import Any, Optional
from sqlalchemy.orm import Query, Session
from app.models.models import (
    User, StudentProfile, ContentItem, Quiz, QuizAttempt,
    UserInteraction, SpacedRepetitionSchedule, ClassAssignment,
    SchoolClass, Flashcard, TopicMastery
)

class TenantScope:
    @staticmethod
    def apply(query: Query, model: Any, user: User) -> Query:
        """
        Applies tenant-scoped filtering to a query based on caller's role and school_id.
        Super-admins and platform admins have global visibility.
        School administrators and teachers are strictly bound to their school_id.
        """
        if user.role in ["super_admin", "admin"]:
            return query

        school_id = user.school_id
        if not school_id:
            # Unassigned staff have access only to global resources (where school_id is NULL)
            if hasattr(model, "school_id"):
                return query.filter(model.school_id == None)
            return query

        if model == User:
            return query.filter(User.school_id == school_id)

        elif model == StudentProfile:
            return query.join(User, StudentProfile.user_id == User.id).filter(User.school_id == school_id)

        elif model == ContentItem:
            return query.filter((ContentItem.school_id == school_id) | (ContentItem.school_id == None))

        elif model == Quiz:
            return query.filter((Quiz.school_id == school_id) | (Quiz.school_id == None))

        elif model == QuizAttempt:
            return query.join(User, QuizAttempt.student_user_id == User.id).filter(User.school_id == school_id)

        elif model == TopicMastery:
            return query.join(User, TopicMastery.student_user_id == User.id).filter(User.school_id == school_id)

        elif model == UserInteraction:
            return query.join(User, UserInteraction.user_id == User.id).filter(User.school_id == school_id)

        elif model == SpacedRepetitionSchedule:
            return query.join(User, SpacedRepetitionSchedule.student_user_id == User.id).filter(User.school_id == school_id)

        elif model == ClassAssignment:
            return query.join(SchoolClass, ClassAssignment.class_id == SchoolClass.id).filter(SchoolClass.school_id == school_id)

        elif model == SchoolClass:
            return query.filter(SchoolClass.school_id == school_id)

        elif hasattr(model, "school_id"):
            return query.filter((model.school_id == school_id) | (model.school_id == None))

        return query

    @classmethod
    def users(cls, db: Session, user: User) -> Query:
        return cls.apply(db.query(User), User, user)

    @classmethod
    def content(cls, db: Session, user: User) -> Query:
        return cls.apply(db.query(ContentItem), ContentItem, user)

    @classmethod
    def quizzes(cls, db: Session, user: User) -> Query:
        return cls.apply(db.query(Quiz), Quiz, user)

    @classmethod
    def attempts(cls, db: Session, user: User) -> Query:
        return cls.apply(db.query(QuizAttempt), QuizAttempt, user)

    @classmethod
    def masteries(cls, db: Session, user: User) -> Query:
        return cls.apply(db.query(TopicMastery), TopicMastery, user)

    @classmethod
    def assignments(cls, db: Session, user: User) -> Query:
        return cls.apply(db.query(ClassAssignment), ClassAssignment, user)
