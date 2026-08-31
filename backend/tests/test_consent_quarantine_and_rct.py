import unittest
import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models.models import User, StudentProfile, ConsentRecord, AuditEvent, ContentItem
from app.core.security import create_access_token
from app.core.consent_service import ConsentService
from app.core.age_policy import ProcessingPurpose
from app.core.ai_budget import AIBudgetManager
from app.core.audit_logger import AuditLogger
from app.safety.ingestion_pipeline import IngestionPipeline


from app.core.redis_client import redis_client


class TestConsentQuarantineAndRCT(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()

    def setUp(self):
        self.db = self.SessionLocal()
        redis_client.clear_all()

    def tearDown(self):
        self.db.close()

    def test_01_consent_revocation_kill_switch(self):
        """Revoking guardian consent for AI Tutoring immediately yields HTTP 403 on tutor endpoint."""
        # Create minor student (age 14)
        student = User(
            id="minor-tutor-killswitch",
            email="minor_killswitch@alpha.edu",
            role="student",
            first_name="Ananya",
            last_name="Roy",
            is_verified=True,
            email_verified=True,
            account_status="ACTIVE",
            token_version=1
        )
        profile = StudentProfile(
            user_id=student.id,
            grade_level=10,
            board="CBSE",
            date_of_birth=datetime.date(2012, 5, 10),
            parental_consent_status="GRANTED"
        )
        guardian = User(
            id="guard-01",
            email="guard01@alpha.edu",
            role="parent",
            first_name="Guardian",
            last_name="Roy"
        )
        self.db.add_all([guardian, student, profile])
        self.db.commit()

        # Grant initial consent
        ConsentService.grant_consent(
            db=self.db,
            student_id=student.id,
            guardian_id=guardian.id,
            purpose=ProcessingPurpose.AI_SOCRATIC_TUTOR.value,
            scope="ai_socratic_tutoring"
        )

        token = create_access_token({"sub": student.email, "role": "student"})
        headers = {"Authorization": f"Bearer {token}"}

        # Query 1: With active consent -> 200 OK
        res1 = self.client.post(
            "/api/v1/tutor/ask",
            headers=headers,
            json={"question": "What is the formula for kinetic energy?"}
        )
        self.assertEqual(res1.status_code, 200)

        # Revoke Consent via Kill Switch
        ConsentService.revoke_consent(
            db=self.db,
            student_id=student.id,
            purpose=ProcessingPurpose.AI_SOCRATIC_TUTOR.value
        )

        # Query 2: Immediate request-time block -> 403 Forbidden
        res2 = self.client.post(
            "/api/v1/tutor/ask",
            headers=headers,
            json={"question": "What is the formula for kinetic energy?"}
        )
        self.assertEqual(res2.status_code, 403)
        self.assertIn("revoked", res2.json()["detail"].lower())

    def test_02_ai_token_quota_enforcement(self):
        """Exceeding daily token limit raises HTTP 429 Too Many Requests."""
        student_id = "quota-test-student"
        
        # 1. Under limit: reserve 500 tokens
        b1 = AIBudgetManager.reserve_budget(
            student_id=student_id,
            estimated_tokens=500,
            student_limit=1000
        )
        self.assertEqual(b1["reserved_tokens"], 500)

        # 2. Exceed remaining 500 tokens limit with request of 600 tokens
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            AIBudgetManager.reserve_budget(
                student_id=student_id,
                estimated_tokens=600,
                student_limit=1000
            )
        self.assertEqual(ctx.exception.status_code, 429)

    def test_03_external_content_quarantine_lifecycle(self):
        """Content candidate moves through Quarantine -> Automated Screening -> Approved / Rejected."""
        # 1. Safe, high pedagogical depth candidate -> APPROVED
        res_approved = IngestionPipeline.process_content_candidate(
            title="Newton's Laws of Motion Comprehensive Analysis",
            description="Detailed breakdown of force, mass, acceleration, inertia, and momentum formulas with worked examples.",
            transcript_text="In this lecture, we examine Newton's second law F=ma, derivation of momentum, and friction calculations.",
            grade_level=10,
            source_url="https://youtube.com/watch?v=newton_safe_physics"
        )
        self.assertEqual(res_approved["moderation_status"], "APPROVED")
        self.assertTrue(res_approved["is_approved"])

        # 2. Dangerous / adversarial candidate -> REJECTED
        res_rejected = IngestionPipeline.process_content_candidate(
            title="Homemade chemical explosives and pipe bomb tutorial",
            description="How to synthesize dangerous materials at home without parental supervision.",
            grade_level=10,
            source_url="https://dangerous-site.org/explosives"
        )
        self.assertEqual(res_rejected["moderation_status"], "REJECTED")
        self.assertFalse(res_rejected["is_approved"])

    def test_04_sequential_audit_concurrency_protection(self):
        """Audit events enforce sequence numbering and tamper-evident verification."""
        user = User(id="auditor-seq-01", email="seq@alpha.edu", role="teacher", first_name="Seq", last_name="Auditor")
        self.db.add(user)
        self.db.commit()

        e1 = AuditLogger.log(db=self.db, actor=user, action="VIEW_RECORD", resource_type="profile", resource_id="001")
        e2 = AuditLogger.log(db=self.db, actor=user, action="VIEW_RECORD", resource_type="profile", resource_id="002")

        self.assertIsNotNone(e1.sequence_number)
        self.assertIsNotNone(e2.sequence_number)
        self.assertEqual(e2.sequence_number, e1.sequence_number + 1)
        self.assertEqual(e2.previous_event_hash, e1.event_hash)

        integrity = AuditLogger.verify_chain_integrity(self.db)
        self.assertTrue(integrity["is_valid"])


if __name__ == "__main__":
    unittest.main()
