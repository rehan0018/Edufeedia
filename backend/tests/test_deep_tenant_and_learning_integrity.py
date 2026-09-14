import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import unittest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.models import (
    School, SchoolClass, User, StudentProfile, ContentItem,
    StudentProgress, Quiz, Question, QuizAttempt, LearningEvent,
    RewardLedger, ConceptNode, PrerequisiteEdge, TopicMastery,
    SpacedRepetitionSchedule
)
from app.core.security import get_password_hash, create_access_token
from app.core.age_policy import StudentAgePolicy, ChildConsentPolicy, AgeBandPolicy
from app.learning.knowledge_graph import KnowledgeGraphEngine


from sqlalchemy.pool import StaticPool

class TestDeepTenantAndLearningIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)
        cls.db = cls.SessionLocal()

        def override_get_db():
            db = cls.SessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

        # 1. Setup Two Distinct Schools
        cls.school_alpha = School(id="school-alpha-001", name="Alpha STEM Academy", domain="alpha.edu")
        cls.school_beta = School(id="school-beta-002", name="Beta Classical Institute", domain="beta.edu")
        cls.db.add_all([cls.school_alpha, cls.school_beta])
        cls.db.commit()

        # 2. Setup School A Students & School B Students
        cls.student_alpha = User(
            id="student-alpha-01",
            email="student1@alpha.edu",
            password_hash=get_password_hash("Secret123!"),
            role="student",
            first_name="Alice",
            last_name="Alpha",
            is_verified=True,
            email_verified=True,
            identity_verified=True,
            account_status="ACTIVE",
            school_id=cls.school_alpha.id,
            token_version=1
        )
        cls.student_beta = User(
            id="student-beta-02",
            email="student2@beta.edu",
            password_hash=get_password_hash("Secret123!"),
            role="student",
            first_name="Bob",
            last_name="Beta",
            is_verified=True,
            email_verified=True,
            identity_verified=True,
            account_status="ACTIVE",
            school_id=cls.school_beta.id,
            token_version=1
        )
        cls.db.add_all([cls.student_alpha, cls.student_beta])
        cls.db.commit()

        # Profiles
        cls.profile_alpha = StudentProfile(
            user_id=cls.student_alpha.id,
            school_id=cls.school_alpha.id,
            grade_level=10,
            board="CBSE",
            date_of_birth=datetime.date(2011, 5, 15),
            onboarding_status="COMPLETED",
            parental_consent_status="GRANTED",
            learning_access_status="ACTIVE"
        )
        cls.profile_beta = StudentProfile(
            user_id=cls.student_beta.id,
            school_id=cls.school_beta.id,
            grade_level=10,
            board="CBSE",
            date_of_birth=datetime.date(2011, 8, 20),
            onboarding_status="COMPLETED",
            parental_consent_status="GRANTED",
            learning_access_status="ACTIVE"
        )
        cls.db.add_all([cls.profile_alpha, cls.profile_beta])
        cls.db.commit()

        # 3. Setup Content Items
        cls.content_alpha = ContentItem(
            id="content-alpha-math",
            title="Alpha Academy Exclusive: Advanced Quadratics",
            description="School Alpha proprietary quadratic factorisation formulas.",
            source_url="https://alpha.edu/lesson/quadratics",
            source_platform="OER_COMMONS",
            type="video",
            duration_minutes=15,
            subject="Mathematics",
            topic="Quadratic Equations",
            grade_level=10,
            board="CBSE",
            school_id=cls.school_alpha.id,
            is_approved=True,
            safety_score=95,
            edu_score=0.88
        )
        cls.content_beta = ContentItem(
            id="content-beta-physics",
            title="Beta Institute Exclusive: Kinematics",
            description="School Beta proprietary projectile motion.",
            source_url="https://beta.edu/lesson/kinematics",
            source_platform="OER_COMMONS",
            type="video",
            duration_minutes=15,
            subject="Physics",
            topic="Kinematics",
            grade_level=10,
            board="CBSE",
            school_id=cls.school_beta.id,
            is_approved=True,
            safety_score=92,
            edu_score=0.85
        )
        cls.content_global = ContentItem(
            id="content-global-chem",
            title="Global Curriculum: Periodic Table",
            description="Open educational resource on periodic trends.",
            source_url="https://khanacademy.org/periodic-table",
            source_platform="KHAN_ACADEMY",
            type="video",
            duration_minutes=15,
            subject="Chemistry",
            topic="Periodic Table",
            grade_level=10,
            board="CBSE",
            school_id=None,
            is_approved=True,
            safety_score=96,
            edu_score=0.90
        )
        cls.db.add_all([cls.content_alpha, cls.content_beta, cls.content_global])
        cls.db.commit()

        cls.token_alpha = create_access_token(
            {"sub": cls.student_alpha.email, "role": "student"},
            token_version=cls.student_alpha.token_version
        )
        cls.token_beta = create_access_token(
            {"sub": cls.student_beta.email, "role": "student"},
            token_version=cls.student_beta.token_version
        )

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        app.dependency_overrides.clear()

    def test_01_tenant_isolation_in_content_get(self):
        """Student A cannot access School B proprietary content item by ID."""
        headers_alpha = {"Authorization": f"Bearer {self.token_alpha}"}
        
        # Student Alpha accesses Alpha content -> 200 OK
        resp = self.client.get(f"/api/v1/content/{self.content_alpha.id}", headers=headers_alpha)
        self.assertEqual(resp.status_code, 200)

        # Student Alpha accesses Global content -> 200 OK
        resp = self.client.get(f"/api/v1/content/{self.content_global.id}", headers=headers_alpha)
        self.assertEqual(resp.status_code, 200)

        # Student Alpha accesses Beta content -> 404 NOT FOUND (tenant boundary protected)
        resp = self.client.get(f"/api/v1/content/{self.content_beta.id}", headers=headers_alpha)
        self.assertEqual(resp.status_code, 404)

    def test_02_tenant_isolation_in_content_explore(self):
        """Explore content returns ONLY the student's school content + global curriculum."""
        headers_alpha = {"Authorization": f"Bearer {self.token_alpha}"}
        resp = self.client.get("/api/v1/content/explore", headers=headers_alpha)
        self.assertEqual(resp.status_code, 200)
        items = resp.json()
        item_ids = {i["id"] for i in items}
        
        self.assertIn(self.content_alpha.id, item_ids)
        self.assertIn(self.content_global.id, item_ids)
        self.assertNotIn(self.content_beta.id, item_ids)

    def test_03_jwt_invalidation_on_token_version_increment(self):
        """When password is reset (token_version incremented), previous active JWT is rejected with 401."""
        stale_token = create_access_token(
            {"sub": self.student_alpha.email, "role": "student"},
            token_version=1
        )
        # Advance token_version on student
        self.student_alpha.token_version = 2
        self.student_alpha.password_changed_at = datetime.datetime.now(datetime.timezone.utc)
        self.db.commit()

        # Request using old token must be rejected with 401
        resp = self.client.get(
            f"/api/v1/content/{self.content_alpha.id}",
            headers={"Authorization": f"Bearer {stale_token}"}
        )
        self.assertEqual(resp.status_code, 401)
        self.assertIn("revoked", resp.json()["detail"].lower())

        # Generate fresh token with current token_version
        fresh_token = create_access_token(
            {"sub": self.student_alpha.email, "role": "student"},
            token_version=2
        )
        resp2 = self.client.get(
            f"/api/v1/content/{self.content_alpha.id}",
            headers={"Authorization": f"Bearer {fresh_token}"}
        )
        self.assertEqual(resp2.status_code, 200)
        
        # Restore token for other tests
        self.__class__.token_alpha = fresh_token

    def test_04_dpdp_child_consent_statutory_evaluation(self):
        """Under DPDP Act 2023 Sec 9, all individuals under 18 are children requiring guardian consent."""
        eval_14 = ChildConsentPolicy.evaluate_consent_requirement(14)
        self.assertTrue(eval_14["is_child"])
        self.assertTrue(eval_14["requires_guardian_consent"])

        eval_17 = ChildConsentPolicy.evaluate_consent_requirement(17)
        self.assertTrue(eval_17["is_child"])
        self.assertTrue(eval_17["requires_guardian_consent"])

        eval_18 = ChildConsentPolicy.evaluate_consent_requirement(18)
        self.assertFalse(eval_18["is_child"])
        self.assertFalse(eval_18["requires_guardian_consent"])

        # Age bands
        self.assertEqual(AgeBandPolicy.get_age_band(11), "BAND_10_12")
        self.assertEqual(AgeBandPolicy.get_age_band(14), "BAND_13_15")
        self.assertEqual(AgeBandPolicy.get_age_band(17), "BAND_16_17")

    def test_05_idempotent_learning_event_and_reward_ledger(self):
        """Progress completions write LearningEvents and disburse XP idempotently via RewardLedger."""
        headers = {"Authorization": f"Bearer {self.token_alpha}"}
        
        # Complete content item
        resp1 = self.client.post("/api/v1/content/progress", json={
            "content_item_id": self.content_alpha.id,
            "progress_percentage": 100
        }, headers=headers)
        self.assertEqual(resp1.status_code, 200)
        self.assertEqual(resp1.json()["xp_earned"], 15)

        # Verify LearningEvent was persisted
        events = self.db.query(LearningEvent).filter(
            LearningEvent.student_user_id == self.student_alpha.id,
            LearningEvent.content_item_id == self.content_alpha.id
        ).all()
        self.assertGreaterEqual(len(events), 1)

        # Duplicate completion request should yield 0 new XP due to RewardLedger deduplication
        resp2 = self.client.post("/api/v1/content/progress", json={
            "content_item_id": self.content_alpha.id,
            "progress_percentage": 100
        }, headers=headers)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["xp_earned"], 0)

        # Verify RewardLedger has exactly 1 entry
        rewards = self.db.query(RewardLedger).filter(
            RewardLedger.student_user_id == self.student_alpha.id,
            RewardLedger.unique_reward_key == f"xp:completion:{self.student_alpha.id}:{self.content_alpha.id}"
        ).all()
        self.assertEqual(len(rewards), 1)

    def test_06_knowledge_graph_prerequisite_diagnosis(self):
        """Diagnoses unmastered prerequisite concepts when topic mastery is low."""
        # Setup Concepts: Factoring (Prereq) -> Quadratic Equations (Target)
        factoring = ConceptNode(
            id="concept-factoring",
            code="MATH_G9_FACTORISATION",
            subject="Mathematics",
            topic="Polynomials and Factorisation",
            name="Polynomial Factorisation by Splitting Middle Term",
            grade_level=9
        )
        quadratics = ConceptNode(
            id="concept-quadratics",
            code="MATH_G10_QUADRATICS",
            subject="Mathematics",
            topic="Quadratic Equations",
            name="Solving Quadratic Equations via Factoring",
            grade_level=10
        )
        self.db.add_all([factoring, quadratics])
        self.db.commit()

        edge = PrerequisiteEdge(
            id="edge-factoring-quad",
            concept_id=quadratics.id,
            prerequisite_concept_id=factoring.id
        )
        self.db.add(edge)
        self.db.commit()

        # Diagnose student gap with no prior mastery
        diag = KnowledgeGraphEngine.diagnose_learning_gaps(
            db=self.db,
            student_id=self.student_alpha.id,
            subject="Mathematics",
            topic="Quadratic Equations"
        )
        self.assertTrue(diag["has_prerequisite_gap"])
        self.assertEqual(len(diag["remediation_concepts"]), 1)
        self.assertEqual(diag["remediation_concepts"][0]["concept_code"], "MATH_G9_FACTORISATION")


if __name__ == "__main__":
    unittest.main()
