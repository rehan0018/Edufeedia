import unittest
import threading
import datetime
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException

from app.main import app
from app.database import Base, get_db
from app.models.models import User, StudentProfile, ConsentRecord, AuditEvent, ContentItem
from app.core.security import create_access_token
from app.core.redis_client import redis_client
from app.core.consent_service import ConsentService
from app.core.age_policy import ProcessingPurpose
from app.core.ai_budget import AIBudgetManager, ModelPricingRegistry
from app.core.audit_logger import AuditLogger
from app.safety.ingestion_pipeline import IngestionPipeline


class TestAIBudgetAndRevalidation(unittest.TestCase):
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

    def test_01_multi_tier_ai_budget_reservation_and_reconciliation(self):
        """Tests 3-tier budget reservation, reconciliation with dynamic pricing, and refund."""
        student_id = "student-budget-01"
        school_id = "school-apex-01"

        # 1. Successful Reservation
        res = AIBudgetManager.reserve_budget(
            student_id=student_id,
            school_id=school_id,
            estimated_tokens=300,
            student_limit=1000,
            school_limit=5000
        )
        self.assertIsNotNone(res["reservation_id"])
        self.assertEqual(res["reserved_tokens"], 300)

        # 2. Reconcile Actual Usage (Actual was 150 tokens -> refunds 150)
        reconciled = AIBudgetManager.reconcile_budget(
            reservation_id=res["reservation_id"],
            student_id=student_id,
            school_id=school_id,
            actual_prompt_tokens=50,
            actual_completion_tokens=100,
            model_name="gpt-4o-mini"
        )
        self.assertEqual(reconciled["total_tokens_consumed"], 150)
        self.assertEqual(reconciled["tokens_consumed_today"], 150)
        self.assertGreater(reconciled["estimated_cost_usd"], 0.0)

        # 3. Model pricing check
        cost = ModelPricingRegistry.calculate_cost("gpt-4o-mini", prompt_tokens=1000, completion_tokens=1000)
        self.assertEqual(cost, round((1000/1e6)*0.15 + (1000/1e6)*0.60, 7))

        # 4. Student Tier Limit Exceeded
        with self.assertRaises(HTTPException) as ctx:
            AIBudgetManager.reserve_budget(
                student_id=student_id,
                school_id=school_id,
                estimated_tokens=900,
                student_limit=1000
            )
        self.assertEqual(ctx.exception.status_code, 429)

    def test_02_strict_consent_revalidation_and_cache_purge(self):
        """Legacy profile consent requires revalidation; revoking purges Redis cache keys."""
        student = User(
            id="student-reval-01",
            email="reval@alpha.edu",
            role="student",
            first_name="Reval",
            last_name="Child"
        )
        # Profile has legacy unverified PENDING status without granular ConsentRecord
        profile = StudentProfile(
            user_id=student.id,
            grade_level=10,
            board="CBSE",
            parental_consent_status="PENDING",
            date_of_birth=datetime.date(2012, 1, 1)
        )
        self.db.add_all([student, profile])
        self.db.commit()

        # Step 1: Query consent -> Denied because unverified requires guardian OTP
        has_consent = ConsentService.has_valid_consent(self.db, student, ProcessingPurpose.AI_SOCRATIC_TUTOR)
        self.assertFalse(has_consent)

        # Step 2: Grant full verified guardian consent
        ConsentService.grant_consent(
            db=self.db,
            student_id=student.id,
            guardian_id="guard-verified-01",
            purpose=ProcessingPurpose.AI_SOCRATIC_TUTOR.value,
            scope="ai_socratic_tutoring",
            method="GUARDIAN_EMAIL_OTP"
        )
        self.assertTrue(ConsentService.has_valid_consent(self.db, student, ProcessingPurpose.AI_SOCRATIC_TUTOR))

        # Step 3: Populate mock session cache in Redis
        redis_client.set(f"tutor:session:{student.id}:context", "active_session_data")
        redis_client.set(f"rec:feed:{student.id}:v1", "active_feed_data")
        self.assertIsNotNone(redis_client.get(f"tutor:session:{student.id}:context"))

        # Step 4: Revoke consent -> purges downstream cache keys
        ConsentService.revoke_consent(self.db, student.id, ProcessingPurpose.AI_SOCRATIC_TUTOR.value)
        self.assertIsNone(redis_client.get(f"tutor:session:{student.id}:context"))
        self.assertIsNone(redis_client.get(f"rec:feed:{student.id}:v1"))

    def test_03_content_provenance_and_re_quarantine_on_drift(self):
        """Content candidate computes SHA-256 hashes and rescreens upon drift."""
        init_res = IngestionPipeline.process_content_candidate(
            title="Introduction to Chemical Bonding",
            description="Ionic and covalent bonding fundamentals for Grade 10 chemistry.",
            transcript_text="Chemical bonds form through electron transfer or sharing.",
            grade_level=10
        )
        self.assertEqual(init_res["moderation_status"], "APPROVED")
        self.assertIsNotNone(init_res["content_hash"])
        self.assertIsNotNone(init_res["transcript_hash"])

        # Title changed to dangerous content -> triggers re-quarantine and rejection
        drift_res = IngestionPipeline.rescreen_if_source_changed(
            current_content_hash=init_res["content_hash"],
            current_transcript_hash=init_res["transcript_hash"],
            current_policy_version=init_res["policy_version"],
            new_title="How to build dangerous chemical explosives at home",
            new_description="Dangerous substance synthesis guide.",
            new_transcript_text=None,
            grade_level=10
        )
        self.assertTrue(drift_res["needs_rescreening"])
        self.assertEqual(drift_res["moderation_status"], "REJECTED")
        self.assertFalse(drift_res["is_approved"])

    def test_04_concurrent_audit_log_writes(self):
        """Multiple concurrent threads logging audit events maintain sequential monotonicity."""
        actor = User(id="audit-concurrent-actor", email="actor@alpha.edu", role="teacher", first_name="A", last_name="B")
        self.db.add(actor)
        self.db.commit()

        events_logged = []
        errors = []

        def worker(thread_idx):
            thread_db = self.SessionLocal()
            try:
                for i in range(5):
                    ev = AuditLogger.log(
                        db=thread_db,
                        actor=actor,
                        action=f"CONCURRENT_ACTION_{thread_idx}_{i}",
                        resource_type="data_item",
                        resource_id=f"item_{thread_idx}_{i}"
                    )
                    events_logged.append(ev)
            except Exception as e:
                errors.append(e)
            finally:
                thread_db.close()

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(errors), 0)
        self.assertEqual(len(events_logged), 20)

        # Verify integrity of sequence numbers and hash chain
        integrity = AuditLogger.verify_chain_integrity(self.db)
        self.assertTrue(integrity["is_valid"])
        self.assertEqual(integrity["total_events_checked"], 20)


if __name__ == "__main__":
    unittest.main()
