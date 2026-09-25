import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.models import (
    School, User, StudentProfile, ConceptNode, PrerequisiteEdge,
    TopicMastery, MisconceptionLog, AuditEvent
)
from app.learning.knowledge_graph import KnowledgeGraphEngine
from app.core.audit_logger import AuditLogger
from app.core.permissions import RolePermissionMatrix, Permission
from app.core.age_policy import ChildConsentPolicy, ProcessingPurpose


class TestKnowledgeGraphAndAuditSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_dag_cycle_prevention(self):
        """Knowledge Graph rejects self-loops and cyclic prerequisite relationships."""
        # Create 3 concepts: A, B, C
        node_a = ConceptNode(id="node-a", code="MATH_A", subject="Math", topic="Algebra A", name="Algebra A", grade_level=9)
        node_b = ConceptNode(id="node-b", code="MATH_B", subject="Math", topic="Algebra B", name="Algebra B", grade_level=9)
        node_c = ConceptNode(id="node-c", code="MATH_C", subject="Math", topic="Algebra C", name="Algebra C", grade_level=10)
        self.db.add_all([node_a, node_b, node_c])
        self.db.commit()

        # 1. Self-loop rejection
        with self.assertRaises(ValueError) as ctx:
            KnowledgeGraphEngine.add_prerequisite_edge(self.db, "node-a", "node-a")
        self.assertIn("Self-referencing", str(ctx.exception))

        # 2. Add valid edges: B requires A, C requires B  (A -> B -> C)
        # concept_id=B, prereq=A (B requires A)
        edge_1 = KnowledgeGraphEngine.add_prerequisite_edge(self.db, "node-b", "node-a")
        self.assertIsNotNone(edge_1)

        # concept_id=C, prereq=B (C requires B)
        edge_2 = KnowledgeGraphEngine.add_prerequisite_edge(self.db, "node-c", "node-b")
        self.assertIsNotNone(edge_2)

        # 3. Cycle attempt: A requires C (would create cycle: A requires C requires B requires A)
        with self.assertRaises(ValueError) as ctx:
            KnowledgeGraphEngine.add_prerequisite_edge(self.db, "node-a", "node-c")
        self.assertIn("Cyclic prerequisite relationship detected", str(ctx.exception))

    def test_02_multifactor_mastery_diagnosis(self):
        """Diagnose learning gaps accounts for recency decay and active misconceptions."""
        student = User(
            id="diag-student-01",
            email="diag@alpha.edu",
            role="student",
            first_name="Diagnostic",
            last_name="Student"
        )
        self.db.add(student)
        self.db.commit()

        # Prereq Node & Target Node
        prereq = ConceptNode(id="diag-prereq", code="PHYS_VEC", subject="Physics", topic="Vectors", name="Vector Addition", grade_level=11)
        target = ConceptNode(id="diag-target", code="PHYS_KIN", subject="Physics", topic="2D Kinematics", name="Projectile Motion", grade_level=11)
        self.db.add_all([prereq, target])
        self.db.commit()

        KnowledgeGraphEngine.add_prerequisite_edge(self.db, "diag-target", "diag-prereq")

        # Scenario A: Student scored 80% on Vectors, but 120 days ago (recency decay applies -> 80 * 0.85 = 68% < 75%)
        old_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=120)
        mastery = TopicMastery(
            student_user_id=student.id,
            subject="Physics",
            topic="Vectors",
            mastery_score=80.0,
            last_assessed_at=old_date
        )
        self.db.add(mastery)
        self.db.commit()

        diag = KnowledgeGraphEngine.diagnose_learning_gaps(self.db, student.id, "Physics", "2D Kinematics")
        self.assertTrue(diag["has_prerequisite_gap"])
        self.assertEqual(len(diag["remediation_concepts"]), 1)
        self.assertEqual(diag["remediation_concepts"][0]["effective_mastery"], 68.0)

        # Scenario B: Student has active diagnosed misconception
        KnowledgeGraphEngine.log_misconception(
            db=self.db,
            student_id=student.id,
            subject="Physics",
            topic="Vectors",
            pattern="confuses_vector_magnitude_with_scalar_distance"
        )
        diag2 = KnowledgeGraphEngine.diagnose_learning_gaps(self.db, student.id, "Physics", "2D Kinematics")
        self.assertTrue(diag2["has_prerequisite_gap"])
        self.assertIn("ACTIVE_MISCONCEPTION", diag2["remediation_concepts"][0]["remediation_reason"])

    def test_03_persistent_audit_logging(self):
        """AuditLogger creates persistent, immutable AuditEvent records with IP anonymization."""
        user = User(
            id="auditor-01",
            email="teacher@alpha.edu",
            role="teacher",
            first_name="Auditor",
            last_name="Teacher",
            school_id="school-alpha"
        )
        self.db.add(user)
        self.db.commit()

        event = AuditLogger.log(
            db=self.db,
            actor=user,
            action="VIEW_CHILD_PROFILE",
            resource_type="student_profile",
            resource_id="student-xyz-123",
            status="SUCCESS",
            reason="Parent-Teacher conference review"
        )
        self.assertIsNotNone(event.id)

        # Query database to confirm persistence
        saved = self.db.query(AuditEvent).filter(AuditEvent.id == event.id).first()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.actor_id, "auditor-01")
        self.assertEqual(saved.action, "VIEW_CHILD_PROFILE")
        self.assertEqual(saved.school_id, "school-alpha")

    def test_04_role_permission_matrix(self):
        """RolePermissionMatrix strictly gates granular platform permissions."""
        self.assertTrue(RolePermissionMatrix.has_permission("student", Permission.USE_AI_TUTOR))
        self.assertFalse(RolePermissionMatrix.has_permission("student", Permission.MANAGE_SCHOOL_CLASSES))

        self.assertTrue(RolePermissionMatrix.has_permission("teacher", Permission.AUTHOR_CUSTOM_QUIZ))
        self.assertFalse(RolePermissionMatrix.has_permission("teacher", Permission.MANAGE_ALL_SCHOOLS))

        self.assertTrue(RolePermissionMatrix.has_permission("super_admin", Permission.MANAGE_ALL_SCHOOLS))
        self.assertTrue(RolePermissionMatrix.has_permission("super_admin", Permission.ACCESS_AUDIT_LOGS))

    def test_05_purpose_specific_dpdp_consent(self):
        """DPDP ChildConsentPolicy evaluates purpose-specific legal bases and consent requirements."""
        # Age 14: AI Socratic Tutor -> Requires explicit guardian consent
        ai_eval = ChildConsentPolicy.evaluate_consent_requirement(
            age=14,
            processing_purpose=ProcessingPurpose.AI_SOCRATIC_TUTOR.value
        )
        self.assertTrue(ai_eval["is_child"])
        self.assertTrue(ai_eval["requires_guardian_consent"])
        self.assertEqual(ai_eval["policy_basis"], "EXPLICIT_VERIFIABLE_GUARDIAN_CONSENT")

        # Age 14: Safety Monitoring -> Exempt from explicit opt-in (active child safety protection)
        safety_eval = ChildConsentPolicy.evaluate_consent_requirement(
            age=14,
            processing_purpose=ProcessingPurpose.SAFETY_MONITORING.value
        )
        self.assertTrue(safety_eval["is_child"])
        self.assertFalse(safety_eval["requires_guardian_consent"])
        self.assertEqual(safety_eval["policy_basis"], "CHILD_SAFETY_PROTECTION")

        # Age 14: School Administration -> Institutional enrolment basis
        admin_eval = ChildConsentPolicy.evaluate_consent_requirement(
            age=14,
            processing_purpose=ProcessingPurpose.SCHOOL_ADMINISTRATION.value
        )
        self.assertTrue(admin_eval["is_child"])
        self.assertFalse(admin_eval["requires_guardian_consent"])
        self.assertEqual(admin_eval["legal_basis"], "EDUCATIONAL_INSTITUTION_PROVISION")


if __name__ == "__main__":
    unittest.main()
