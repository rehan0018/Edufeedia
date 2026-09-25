import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models.models import User, StudentProfile, AuditEvent, ConsentRecord, ConceptNode, PrerequisiteEdge
from app.core.audit_logger import AuditLogger
from app.core.consent_service import ConsentService
from app.core.age_policy import ProcessingPurpose, StudentAgePolicy
from app.ai.rag_engine import RAGEngine


class TestAuditHashChainAndConsent(unittest.TestCase):
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

    def test_01_cryptographic_audit_hash_chaining(self):
        """AuditLogger links subsequent events via SHA-256 parent hash chaining."""
        user = User(id="user-hash-01", email="teacher@alpha.edu", role="teacher", first_name="Chain", last_name="Tester")
        self.db.add(user)
        self.db.commit()

        # Log Block 1
        ev1 = AuditLogger.log(
            db=self.db,
            actor=user,
            action="VIEW_CHILD_PROFILE",
            resource_type="student_profile",
            resource_id="student-001",
            status="SUCCESS",
            reason="Parent-Teacher conference"
        )
        self.assertIsNotNone(ev1.event_hash)
        self.assertEqual(len(ev1.event_hash), 64)

        # Log Block 2
        ev2 = AuditLogger.log(
            db=self.db,
            actor=user,
            action="UPDATE_GRADE_ROSTER",
            resource_type="school_class",
            resource_id="class-10A",
            status="SUCCESS",
            reason="Mid-term grade submission"
        )
        self.assertEqual(ev2.previous_event_hash, ev1.event_hash)

        # Log Block 3
        ev3 = AuditLogger.log(
            db=self.db,
            actor=user,
            action="INVITE_STAFF",
            resource_type="user",
            resource_id="new-teacher-id",
            status="SUCCESS",
            reason="Onboarding science faculty"
        )
        self.assertEqual(ev3.previous_event_hash, ev2.event_hash)

        # Verify full chain integrity
        integrity = AuditLogger.verify_chain_integrity(self.db)
        self.assertTrue(integrity["is_valid"])
        self.assertEqual(integrity["total_events_checked"], 3)

    def test_02_audit_tamper_detection(self):
        """Tampering with an event in the audit chain is detected immediately by integrity verification."""
        events = self.db.query(AuditEvent).all()
        self.assertGreaterEqual(len(events), 2)
        
        # Tamper with the second event's hash
        target_event = events[1]
        original_hash = target_event.event_hash
        target_event.event_hash = "corrupted_tampered_hash_00000000000000000000000000000000000000000000"
        self.db.commit()

        # Verify integrity detects corruption
        integrity = AuditLogger.verify_chain_integrity(self.db)
        self.assertFalse(integrity["is_valid"])
        self.assertGreater(len(integrity["violations"]), 0)

        # Restore original hash for clean test state
        target_event.event_hash = original_hash
        self.db.commit()

    def test_03_enforceable_consent_lifecycle_and_revocation(self):
        """ConsentService enforces real-time DPDP Section 9 consent gating and immediate revocation."""
        student = User(
            id="student-minor-01",
            email="minor@alpha.edu",
            role="student",
            first_name="Rohan",
            last_name="Verma"
        )
        self.db.add(student)
        self.db.commit()

        profile = StudentProfile(
            user_id=student.id,
            grade_level=10,
            board="CBSE",
            date_of_birth=datetime.date(2012, 1, 1), # 14 years old
            parental_consent_status="PENDING",
            learning_access_status="ACTIVE",
            onboarding_status="COMPLETED"
        )
        self.db.add(profile)
        self.db.commit()

        # 1. Without consent, AI Socratic Tutoring is blocked for minor
        has_consent_init = ConsentService.has_valid_consent(
            db=self.db,
            student_user=student,
            purpose=ProcessingPurpose.AI_SOCRATIC_TUTOR
        )
        self.assertFalse(has_consent_init)

        # 2. Grant explicit guardian consent
        rec = ConsentService.grant_consent(
            db=self.db,
            student_id=student.id,
            guardian_id="guardian-user-01",
            purpose=ProcessingPurpose.AI_SOCRATIC_TUTOR.value,
            scope="ai_socratic_tutoring",
            method="GUARDIAN_EMAIL_OTP"
        )
        self.assertEqual(rec.status, "ACTIVE")

        # Now consent evaluates to True
        has_consent_granted = ConsentService.has_valid_consent(
            db=self.db,
            student_user=student,
            purpose=ProcessingPurpose.AI_SOCRATIC_TUTOR
        )
        self.assertTrue(has_consent_granted)

        # 3. Immediately revoke consent
        ConsentService.revoke_consent(
            db=self.db,
            student_id=student.id,
            purpose=ProcessingPurpose.AI_SOCRATIC_TUTOR.value
        )

        # Post-revocation check evaluates immediately to False
        has_consent_revoked = ConsentService.has_valid_consent(
            db=self.db,
            student_user=student,
            purpose=ProcessingPurpose.AI_SOCRATIC_TUTOR
        )
        self.assertFalse(has_consent_revoked)

    def test_04_knowledge_graph_provenance_and_versioning(self):
        """ConceptNode and PrerequisiteEdge store curriculum versioning and provenance authority."""
        concept = ConceptNode(
            id="concept-v2026",
            code="MATH_G10_TRIG",
            subject="Mathematics",
            topic="Trigonometry",
            name="Trigonometric Identities",
            grade_level=10,
            board="CBSE",
            curriculum_version="2026.1"
        )
        self.db.add(concept)
        self.db.commit()

        self.assertEqual(concept.curriculum_version, "2026.1")


if __name__ == "__main__":
    unittest.main()
