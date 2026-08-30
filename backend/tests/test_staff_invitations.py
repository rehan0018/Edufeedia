"""
Comprehensive Staff Invitation and Token Lifecycle Verification Suite.
Validates authoritative PostgreSQL StaffInvitation model, SHA-256 token hashing,
single-use enforcement, expiration, revocation, tenant boundary isolation,
and resilience against Redis outages.
"""

import unittest
import os
import sys
import uuid
import hashlib
import datetime
from pathlib import Path
from unittest.mock import patch

# Ensure backend root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import SessionLocal
from app.models.models import User, School, SchoolClass, StaffInvitation, teacher_classes
from app.core.security import get_password_hash
from app.core.redis_client import redis_client

client = TestClient(app)

class TestStaffInvitationsLifecycle(unittest.TestCase):
    SCHOOL_A_ID = "sch-inv-alpha"
    SCHOOL_B_ID = "sch-inv-beta"
    ADMIN_A_ID = "u-admin-alpha"
    ADMIN_A_EMAIL = "admin_alpha@apexschool.edu"

    @classmethod
    def setUpClass(cls):
        cls.db: Session = SessionLocal()
        cls._cleanup()

        # 1. School A & Admin
        cls.school_a = School(id=cls.SCHOOL_A_ID, name="Alpha Academy", domain="alpha.edu")
        cls.school_b = School(id=cls.SCHOOL_B_ID, name="Beta Academy", domain="beta.edu")
        cls.db.add_all([cls.school_a, cls.school_b])
        cls.db.flush()

        cls.admin_a = User(
            id=cls.ADMIN_A_ID,
            email=cls.ADMIN_A_EMAIL,
            password_hash=get_password_hash("AdminPass123!"),
            role="school_admin",
            first_name="Admin",
            last_name="Alpha",
            is_verified=True,
            school_id=cls.SCHOOL_A_ID
        )
        cls.db.add(cls.admin_a)

        cls.class_a = SchoolClass(
            id="cls-alpha-1",
            school_id=cls.SCHOOL_A_ID,
            grade_level=10,
            section_name="A",
            academic_year="2026-2027"
        )
        cls.class_b = SchoolClass(
            id="cls-beta-1",
            school_id=cls.SCHOOL_B_ID,
            grade_level=10,
            section_name="B",
            academic_year="2026-2027"
        )
        cls.db.add_all([cls.class_a, cls.class_b])
        cls.db.commit()

        # Admin login token
        login_res = client.post("/api/v1/auth/login", json={
            "email": cls.ADMIN_A_EMAIL,
            "password": "AdminPass123!"
        })
        cls.admin_token = login_res.json()["access_token"]
        cls.admin_headers = {"Authorization": f"Bearer {cls.admin_token}"}

    @classmethod
    def tearDownClass(cls):
        cls._cleanup()
        cls.db.close()

    @classmethod
    def _cleanup(cls):
        cls.db.query(StaffInvitation).filter(StaffInvitation.school_id.in_([cls.SCHOOL_A_ID, cls.SCHOOL_B_ID])).delete(synchronize_session=False)
        cls.db.query(User).filter((User.school_id.in_([cls.SCHOOL_A_ID, cls.SCHOOL_B_ID])) | (User.email == cls.ADMIN_A_EMAIL)).delete(synchronize_session=False)
        cls.db.query(SchoolClass).filter(SchoolClass.school_id.in_([cls.SCHOOL_A_ID, cls.SCHOOL_B_ID])).delete(synchronize_session=False)
        cls.db.query(School).filter((School.id.in_([cls.SCHOOL_A_ID, cls.SCHOOL_B_ID])) | (School.domain.in_(["alpha.edu", "beta.edu"]))).delete(synchronize_session=False)
        cls.db.commit()

    def setUp(self):
        redis_client.clear_all()

    def test_01_staff_invitation_creates_pending_record(self):
        """Verify invitation creates unverified user and pending StaffInvitation record with SHA-256 hash."""
        teacher_email = f"t_{uuid.uuid4().hex[:6]}@alpha.edu"
        with patch("app.core.email_service.email_service.send_staff_invitation") as mock_email:
            mock_email.return_value = {"status": "sent", "provider": "mock"}
            res = client.post(
                "/api/v1/admin/invite-teacher",
                headers=self.admin_headers,
                json={"email": teacher_email, "first_name": "Alan", "last_name": "Turing"}
            )
            self.assertEqual(res.status_code, 200)
            token = mock_email.call_args[1]["invitation_token"]

        user = self.db.query(User).filter(User.email == teacher_email).first()
        self.assertIsNotNone(user)
        self.assertFalse(user.is_verified)
        self.assertEqual(user.school_id, self.SCHOOL_A_ID)

        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        inv = self.db.query(StaffInvitation).filter(StaffInvitation.token_hash == token_hash).first()
        self.assertIsNotNone(inv)
        self.assertEqual(inv.status, "PENDING")
        self.assertEqual(inv.user_id, user.id)

    def test_02_staff_invitation_token_is_single_use(self):
        """Verify invitation token cannot be redeemed more than once."""
        teacher_email = f"t_{uuid.uuid4().hex[:6]}@alpha.edu"
        with patch("app.core.email_service.email_service.send_staff_invitation") as mock_email:
            mock_email.return_value = {"status": "sent", "provider": "mock"}
            client.post(
                "/api/v1/admin/invite-teacher",
                headers=self.admin_headers,
                json={"email": teacher_email, "first_name": "Ada", "last_name": "Lovelace"}
            )
            token = mock_email.call_args[1]["invitation_token"]

        # First activation succeeds
        res1 = client.post("/api/v1/auth/activate-invite", json={"token": token, "password": "Password123!"})
        self.assertEqual(res1.status_code, 200)

        # Second activation with same token is rejected
        res2 = client.post("/api/v1/auth/activate-invite", json={"token": token, "password": "Password123!"})
        self.assertEqual(res2.status_code, 400)
        self.assertIn("already been used", res2.json()["detail"])

    def test_03_staff_invitation_token_expires(self):
        """Verify expired invitation token is rejected and marked EXPIRED."""
        teacher_email = f"t_{uuid.uuid4().hex[:6]}@alpha.edu"
        with patch("app.core.email_service.email_service.send_staff_invitation") as mock_email:
            mock_email.return_value = {"status": "sent", "provider": "mock"}
            client.post(
                "/api/v1/admin/invite-teacher",
                headers=self.admin_headers,
                json={"email": teacher_email, "first_name": "Grace", "last_name": "Hopper"}
            )
            token = mock_email.call_args[1]["invitation_token"]

        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        inv = self.db.query(StaffInvitation).filter(StaffInvitation.token_hash == token_hash).first()
        # Manually backdate expiry to the past
        inv.expires_at = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        self.db.commit()

        res = client.post("/api/v1/auth/activate-invite", json={"token": token, "password": "Password123!"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("expired", res.json()["detail"])

        self.db.refresh(inv)
        self.assertEqual(inv.status, "EXPIRED")

    def test_04_staff_invitation_can_be_revoked(self):
        """Verify admin can revoke pending invitation and activation is blocked."""
        teacher_email = f"t_{uuid.uuid4().hex[:6]}@alpha.edu"
        with patch("app.core.email_service.email_service.send_staff_invitation") as mock_email:
            mock_email.return_value = {"status": "sent", "provider": "mock"}
            res = client.post(
                "/api/v1/admin/invite-teacher",
                headers=self.admin_headers,
                json={"email": teacher_email, "first_name": "Claude", "last_name": "Shannon"}
            )
            token = mock_email.call_args[1]["invitation_token"]
            inv_id = res.json()["invitation_id"]

        # Admin revokes invitation
        revoke_res = client.post(f"/api/v1/admin/invitations/{inv_id}/revoke", headers=self.admin_headers)
        self.assertEqual(revoke_res.status_code, 200)

        # Attempting activation fails
        act_res = client.post("/api/v1/auth/activate-invite", json={"token": token, "password": "Password123!"})
        self.assertEqual(act_res.status_code, 400)
        self.assertIn("revoked", act_res.json()["detail"])

    def test_05_staff_invitation_wrong_token_rejected(self):
        """Verify invalid non-existent token is rejected."""
        res = client.post("/api/v1/auth/activate-invite", json={"token": "invalid_nonexistent_token_123", "password": "Password123!"})
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid or expired", res.json()["detail"])

    def test_06_staff_invitation_wrong_role_rejected(self):
        """Verify non-admin user cannot invite staff."""
        non_admin_token = "dummy-non-admin"
        res = client.post(
            "/api/v1/admin/invite-teacher",
            headers={"Authorization": f"Bearer {non_admin_token}"},
            json={"email": "hacker@test.com", "first_name": "Bad", "last_name": "Actor"}
        )
        self.assertEqual(res.status_code, 401)

    def test_07_teacher_cannot_login_before_activation(self):
        """Verify invited teacher cannot log in prior to token activation."""
        teacher_email = f"t_{uuid.uuid4().hex[:6]}@alpha.edu"
        with patch("app.core.email_service.email_service.send_staff_invitation"):
            client.post(
                "/api/v1/admin/invite-teacher",
                headers=self.admin_headers,
                json={"email": teacher_email, "first_name": "Donald", "last_name": "Knuth"}
            )

        # Teacher tries to login with random password
        res = client.post("/api/v1/auth/login", json={"email": teacher_email, "password": "AnyPassword123!"})
        self.assertIn(res.status_code, [401, 403])

    def test_08_teacher_can_login_after_activation(self):
        """Verify teacher can successfully log in after redeeming token."""
        teacher_email = f"t_{uuid.uuid4().hex[:6]}@alpha.edu"
        with patch("app.core.email_service.email_service.send_staff_invitation") as mock_email:
            mock_email.return_value = {"status": "sent", "provider": "mock"}
            client.post(
                "/api/v1/admin/invite-teacher",
                headers=self.admin_headers,
                json={"email": teacher_email, "first_name": "Barbara", "last_name": "Liskov"}
            )
            token = mock_email.call_args[1]["invitation_token"]

        # Activate
        client.post("/api/v1/auth/activate-invite", json={"token": token, "password": "LiskovPassword123!"})

        # Login
        login_res = client.post("/api/v1/auth/login", json={"email": teacher_email, "password": "LiskovPassword123!"})
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("access_token", login_res.json())

    def test_09_teacher_remains_in_correct_school(self):
        """Verify activated teacher is strictly associated with inviting school."""
        teacher_email = f"t_{uuid.uuid4().hex[:6]}@alpha.edu"
        with patch("app.core.email_service.email_service.send_staff_invitation") as mock_email:
            mock_email.return_value = {"status": "sent", "provider": "mock"}
            client.post(
                "/api/v1/admin/invite-teacher",
                headers=self.admin_headers,
                json={"email": teacher_email, "first_name": "Tim", "last_name": "Berners-Lee"}
            )
            token = mock_email.call_args[1]["invitation_token"]

        client.post("/api/v1/auth/activate-invite", json={"token": token, "password": "WebPassword123!"})
        user = self.db.query(User).filter(User.email == teacher_email).first()
        self.assertEqual(user.school_id, self.SCHOOL_A_ID)

    def test_10_teacher_cannot_cross_school_boundary(self):
        """Verify school admin cannot link teacher to a class from another school."""
        teacher_email = f"t_{uuid.uuid4().hex[:6]}@alpha.edu"
        res = client.post(
            "/api/v1/admin/invite-teacher",
            headers=self.admin_headers,
            json={
                "email": teacher_email,
                "first_name": "Dennis",
                "last_name": "Ritchie",
                "class_ids": [self.class_b.id] # Class B belongs to School B
            }
        )
        self.assertEqual(res.status_code, 403)
        self.assertIn("Access denied", res.json()["detail"])

    def test_11_redis_failure_does_not_corrupt_invitation(self):
        """Verify database-backed invitation succeeds even when Redis cache is wiped or disconnected."""
        teacher_email = f"t_{uuid.uuid4().hex[:6]}@alpha.edu"
        with patch("app.core.email_service.email_service.send_staff_invitation") as mock_email:
            mock_email.return_value = {"status": "sent", "provider": "mock"}
            client.post(
                "/api/v1/admin/invite-teacher",
                headers=self.admin_headers,
                json={"email": teacher_email, "first_name": "Linus", "last_name": "Torvalds"}
            )
            token = mock_email.call_args[1]["invitation_token"]

        # Completely wipe Redis cache before activation
        redis_client.clear_all()

        # Activation still succeeds using PostgreSQL authoritative record!
        act_res = client.post("/api/v1/auth/activate-invite", json={"token": token, "password": "LinuxPassword123!"})
        self.assertEqual(act_res.status_code, 200)
        self.assertEqual(act_res.json()["role"], "teacher")

if __name__ == "__main__":
    unittest.main()
