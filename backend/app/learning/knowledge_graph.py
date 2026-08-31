"""
Curriculum Knowledge Graph & Prerequisite Diagnostic Engine.
Provides directed acyclic graph (DAG) traversal across K-12 concepts to identify root learning gaps.
Enforces strict cycle rejection on prerequisite creation and multi-factor mastery evaluation.
"""

from typing import List, Dict, Any, Optional, Set
from collections import deque
import datetime
from sqlalchemy.orm import Session

from app.models.models import ConceptNode, PrerequisiteEdge, TopicMastery, MisconceptionLog


class KnowledgeGraphEngine:
    """
    Manages concept nodes, prerequisite relationships, cycle detection, and adaptive remediation pathways.
    """

    @classmethod
    def is_reachable(cls, db: Session, start_concept_id: str, target_concept_id: str) -> bool:
        """
        Determines if target_concept_id can be reached from start_concept_id via prerequisite edges.
        Uses BFS traversal to prevent infinite loops.
        """
        if start_concept_id == target_concept_id:
            return True

        visited: Set[str] = {start_concept_id}
        queue: deque = deque([start_concept_id])

        while queue:
            curr = queue.popleft()
            edges = db.query(PrerequisiteEdge).filter(PrerequisiteEdge.concept_id == curr).all()
            for edge in edges:
                neighbor = edge.prerequisite_concept_id
                if neighbor == target_concept_id:
                    return True
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return False

    @classmethod
    def add_prerequisite_edge(
        cls,
        db: Session,
        concept_id: str,
        prerequisite_concept_id: str,
        weight: float = 1.0
    ) -> PrerequisiteEdge:
        """
        Inserts a prerequisite relationship (concept_id requires prerequisite_concept_id).
        Enforces DAG integrity: Rejects self-loops and any edge that would create a directed cycle.
        """
        if concept_id == prerequisite_concept_id:
            raise ValueError(f"Self-referencing prerequisite edges are prohibited: {concept_id} -> {concept_id}")

        # Check if prerequisite_concept_id can already reach concept_id (which would create a cycle)
        if cls.is_reachable(db, start_concept_id=prerequisite_concept_id, target_concept_id=concept_id):
            raise ValueError(
                f"Cyclic prerequisite relationship detected: Concept '{prerequisite_concept_id}' "
                f"already reaches '{concept_id}'. Adding this edge violates DAG constraints."
            )

        # Check if edge already exists
        existing = db.query(PrerequisiteEdge).filter(
            PrerequisiteEdge.concept_id == concept_id,
            PrerequisiteEdge.prerequisite_concept_id == prerequisite_concept_id
        ).first()
        if existing:
            return existing

        edge = PrerequisiteEdge(
            concept_id=concept_id,
            prerequisite_concept_id=prerequisite_concept_id,
            weight=weight
        )
        db.add(edge)
        db.commit()
        db.refresh(edge)
        return edge

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
        Multi-factor prerequisite diagnostic engine.
        Evaluates mastery score, recency decay, score trends, and active cognitive misconceptions
        to find root prerequisite deficiencies.
        """
        concepts = db.query(ConceptNode).filter(
            ConceptNode.subject.ilike(f"%{subject}%"),
            ConceptNode.topic.ilike(f"%{topic}%")
        ).all()

        unmastered_prereqs = []
        now = datetime.datetime.now(datetime.timezone.utc)

        for concept in concepts:
            prereqs = cls.get_prerequisites(db, concept.id)
            for prereq in prereqs:
                # 1. Topic Mastery Check
                mastery = db.query(TopicMastery).filter(
                    TopicMastery.student_user_id == student_id,
                    TopicMastery.subject == prereq.subject,
                    TopicMastery.topic.ilike(f"%{prereq.topic}%")
                ).first()

                # 2. Check for unresolved diagnosed misconceptions
                active_misconception = db.query(MisconceptionLog).filter(
                    MisconceptionLog.student_user_id == student_id,
                    MisconceptionLog.subject == prereq.subject,
                    MisconceptionLog.resolved_at.is_(None)
                ).first()

                raw_score = float(mastery.mastery_score) if mastery else 0.0
                effective_score = raw_score
                needs_remediation = False
                remediation_reason = "UNASSESSED"

                if not mastery:
                    needs_remediation = True
                    remediation_reason = "PREREQUISITE_NOT_YET_STUDIED"
                else:
                    # Factor in recency decay if assessed > 90 days ago
                    if mastery.last_assessed_at:
                        last_assessed = mastery.last_assessed_at
                        if last_assessed.tzinfo is None:
                            last_assessed = last_assessed.replace(tzinfo=datetime.timezone.utc)
                        days_since = (now - last_assessed).days
                        if days_since > 90:
                            effective_score = max(0.0, effective_score * 0.85)

                    # Factor in active misconception
                    if active_misconception:
                        needs_remediation = True
                        remediation_reason = f"ACTIVE_MISCONCEPTION: {active_misconception.pattern}"
                    elif effective_score < 75.0:
                        needs_remediation = True
                        remediation_reason = f"MASTERY_BELOW_THRESHOLD ({round(effective_score, 1)}%)"

                if needs_remediation:
                    unmastered_prereqs.append({
                        "concept_code": prereq.code,
                        "concept_name": prereq.name,
                        "topic": prereq.topic,
                        "subject": prereq.subject,
                        "grade_level": prereq.grade_level,
                        "raw_mastery": raw_score,
                        "effective_mastery": round(effective_score, 1),
                        "remediation_reason": remediation_reason,
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
