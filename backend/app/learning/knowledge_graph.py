"""
Curriculum Knowledge Graph & Prerequisite Diagnostic Engine.
Provides directed acyclic graph (DAG) traversal across K-12 concepts to identify root learning gaps.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.models import ConceptNode, PrerequisiteEdge, TopicMastery, MisconceptionLog
import datetime


class KnowledgeGraphEngine:
    """
    Manages concept nodes, prerequisite relationships, and adaptive remediation pathways.
    """

    @classmethod
    def get_prerequisites(cls, db: Session, concept_id: str) -> List[ConceptNode]:
        """
        Retrieves direct prerequisite concepts required before mastering this concept.
        """
        edges = db.query(PrerequisiteEdge).filter(PrerequisiteEdge.concept_id == concept_id).all()
        prereq_ids = [e.prerequisite_concept_id for e in edges]
        if not prereq_ids:
            return []
        return db.query(ConceptNode).filter(ConceptNode.id.in_(prereq_ids)).all()

    @classmethod
    def diagnose_learning_gaps(
        cls,
        db: Session,
        student_id: str,
        subject: str,
        topic: str
    ) -> Dict[str, Any]:
        """
        Identifies whether a student's struggle in a topic stems from an unmastered prerequisite concept.
        """
        # Find matching concept nodes
        concepts = db.query(ConceptNode).filter(
            ConceptNode.subject.ilike(f"%{subject}%"),
            ConceptNode.topic.ilike(f"%{topic}%")
        ).all()

        unmastered_prereqs = []
        for concept in concepts:
            prereqs = cls.get_prerequisites(db, concept.id)
            for prereq in prereqs:
                # Check student's mastery in the prerequisite topic
                mastery = db.query(TopicMastery).filter(
                    TopicMastery.student_user_id == student_id,
                    TopicMastery.subject == prereq.subject,
                    TopicMastery.topic.ilike(f"%{prereq.topic}%")
                ).first()

                if not mastery or mastery.mastery_score < 70:
                    unmastered_prereqs.append({
                        "concept_code": prereq.code,
                        "concept_name": prereq.name,
                        "topic": prereq.topic,
                        "subject": prereq.subject,
                        "grade_level": prereq.grade_level,
                        "current_mastery": mastery.mastery_score if mastery else 0.0,
                        "is_missing": mastery is None
                    })

        return {
            "target_subject": subject,
            "target_topic": topic,
            "has_prerequisite_gap": len(unmastered_prereqs) > 0,
            "remediation_concepts": unmastered_prereqs
        }

    @classmethod
    def log_misconception(
        cls,
        db: Session,
        student_id: str,
        subject: str,
        topic: str,
        pattern: str,
        concept_code: Optional[str] = None,
        confidence: float = 0.85
    ) -> MisconceptionLog:
        """
        Records a diagnosed student cognitive misconception into the longitudinal learning record.
        """
        log = MisconceptionLog(
            student_user_id=student_id,
            subject=subject,
            topic=topic,
            concept_code=concept_code,
            pattern=pattern,
            confidence=confidence,
            first_seen_at=datetime.datetime.now(datetime.timezone.utc)
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

