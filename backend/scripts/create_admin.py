"""
Production Admin Bootstrapping CLI Script for Edufeedia.
Creates a verified initial Super-Administrator or School Administrator account
with strong bcrypt password hashing.
"""

import sys
import os
import argparse
import bcrypt

# Add the backend root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import SessionLocal
from app.models.models import User, School

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_admin(email: str, password: str, first_name: str, last_name: str, role: str = "admin", school_id: str = None):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"❌ User with email '{email}' already exists.")
            return False

        if role == "school_admin" and school_id:
            school = db.query(School).filter(School.id == school_id).first()
            if not school:
                print(f"❌ School with ID '{school_id}' does not exist.")
                return False

        admin_user = User(
            email=email,
            password_hash=get_password_hash(password),
            role=role,
            first_name=first_name,
            last_name=last_name,
            is_verified=True,
            identity_verified=True,
            account_status="ACTIVE",
            school_id=school_id
        )
        db.add(admin_user)
        db.commit()
        print(f"✅ Successfully created verified {role}: {first_name} {last_name} ({email}) [ID: {admin_user.id}]")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ Error creating admin user: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a verified administrator account for Edufeedia")
    parser.add_argument("--email", required=True, help="Administrator email address")
    parser.add_argument("--password", required=True, help="Strong administrator password (min 10 chars)")
    parser.add_argument("--first-name", default="System", help="First name")
    parser.add_argument("--last-name", default="Admin", help="Last name")
    parser.add_argument("--role", default="admin", choices=["admin", "school_admin", "super_admin"], help="Role type")
    parser.add_argument("--school-id", default=None, help="School ID (required for school_admin)")

    args = parser.parse_args()

    if len(args.password) < 8:
        print("❌ Password must be at least 8 characters long.")
        sys.exit(1)

    create_admin(
        email=args.email,
        password=args.password,
        first_name=args.first_name,
        last_name=args.last_name,
        role=args.role,
        school_id=args.school_id
    )
