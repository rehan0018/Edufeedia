import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import threading
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException

from app.database import Base
from app.models.models import User, School, StudentProfile, ConsentRecord, AuditEvent, ContentItem, AIUsageEvent
from app.core.redis_client import redis_client
from app.core.consent_service import ConsentService
from app.core.age_policy import ProcessingPurpose
from app.core.ai_budget import AIBudgetManager, ModelPricingTable
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

    def setUp(self):
        self.db = self.SessionLocal()
        redis_client.clear_all()

    def tearDown(self):
        pass

    def test_01_multi_tier_ai_budget_reservation_and_reconciliation(self):
        """Tests 3-tier budget reservation, reconciliation with strict pricing, and DB event persistence."""
        school = School(id="school-apex-01", name="Apex High School", domain="apex.edu")
        student = User(id="stu-budget-01", school_id=school.id, email="stubudget@alpha.edu", role="student", first_name="A", last_name="B")
        self.db.add_all([school, student])
        self.db.commit()

        student_id = student.id
        school_id = school.id

        # 1. Successful Reservation via Lua script
        res = AIBudgetManager.reserve_budget(
            student_id=student_id,
            school_id=school_id,
            estimated_tokens=300,
            student_limit=1000,
            school_limit=5000,
            platform_limit=50000
        )
        self.assertIsNotNone(res["reservation_id"])
        self.assertEqual(res["reserved_tokens"], 300)

        # 2. Reconcile Actual Usage (Actual was 150 tokens) and persist AIUsageEvent
        reconciled = AIBudgetManager.reconcile_budget(
            reservation_id=res["reservation_id"],
            student_id=student_id,
            school_id=school_id,
            actual_prompt_tokens=50,
            actual_completion_tokens=100,
            model_name="gpt-4o-mini",
            request_id="req-test-101",
            db=self.db
        )
        self.assertEqual(reconciled["total_tokens_consumed"], 150)
        self.assertEqual(reconciled["tokens_consumed_today"], 150)
        self.assertGreater(reconciled["estimated_cost_usd"], 0.0)

        # Verify persistent AIUsageEvent in DB
        event = self.db.query(AIUsageEvent).filter(AIUsageEvent.student_id == student_id).first()
        self.assertIsNotNone(event)
        self.assertEqual(event.total_tokens, 150)
        self.assertEqual(event.request_id, "req-test-101")
        self.assertEqual(event.model, "gpt-4o-mini")

        # 3. Model pricing calculation
        cost = ModelPricingTable.calculate_cost("gpt-4o-mini", prompt_tokens=1000, completion_tokens=1000)
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

    def test_02_unknown_model_strict_rejection(self):
        """Fails closed if an unpriced model is requested."""
        with self.assertRaises(HTTPException) as ctx:
            ModelPricingTable.calculate_cost("gpt-5-unreleased", prompt_tokens=100, completion_tokens=100)
        self.assertEqual(ctx.exception.status_code, 400)

    def test_03_reservation_refund_releases_active_reservation(self):
        """Rolling back reservation decrements active reservation without charging permanent usage."""
        student_id = "stu-refund-01"
        res = AIBudgetManager.reserve_budget(
            student_id=student_id,
            school_id="school-01",
            estimated_tokens=400,
            student_limit=1000
        )
        # Refund
        AIBudgetManager.refund_reservation(res)

        # Now student can reserve full 1000 tokens again
        res2 = AIBudgetManager.reserve_budget(
            student_id=student_id,
            school_id="school-01",
            estimated_tokens=1000,
            student_limit=1000
        )
        self.assertIsNotNone(res2["reservation_id"])

    def test_04_strict_consent_revalidation_and_cache_purge(self):
        """Legacy profile consent requires revalidation; revoking purges Redis cache keys."""
        guardian = User(id="guard-reval-01", email="guard@alpha.edu", role="parent", first_name="P", last_name="Q")
        student = User(id="student-reval-01", email="reval@alpha.edu", role="student", first_name="Reval", last_name="Child")
        profile = StudentProfile(
            user_id=student.id,
            grade_level=10,
            board="CBSE",
            parental_consent_status="LEGACY_PENDING_REVALIDATION",  # Legacy status requiring revalidation
            date_of_birth=datetime.date(2012, 1, 1)
        )
        self.db.add_all([guardian, student, profile])
        self.db.commit()

        # Step 1: Query consent -> Denied because legacy profile is pending revalidation
        has_consent = ConsentService.has_valid_consent(self.db, student, ProcessingPurpose.AI_SOCRATIC_TUTOR)
        self.assertFalse(has_consent)
        self.assertEqual(profile.parental_consent_status, "LEGACY_PENDING_REVALIDATION")

        # Step 2: Grant full verified guardian consent
        ConsentService.grant_consent(
            db=self.db,
            student_id=student.id,
            guardian_id=guardian.id,
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

    def test_05_content_provenance_and_re_quarantine_on_drift(self):
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

    def test_06_concurrent_audit_log_writes(self):
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
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestAIBudgetAndRevalidation)
    runner = unittest.TextTestRunner(verbosity=2)
    res = runner.run(suite)
    import os
    os._exit(0 if len(res.failures) == 0 and len(res.errors) == 0 else 1)
