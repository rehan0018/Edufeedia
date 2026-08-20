import secrets
from datetime import timedelta, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, StudentProfile, parent_student_links
from app.schemas.schemas import UserRegister, UserLogin, Token, UserOut
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    validate_password_complexity, revoke_token, oauth2_scheme
)

router = APIRouter(prefix="/auth", tags=["auth"])

from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from app.core.redis_client import redis_client
from app.core.email_service import email_service

class InviteActivationRequest(BaseModel):
    token: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """
    Public Registration Endpoint: Strictly restricted to Student accounts only.
    Teachers and School Administrators must be invited by authorized school administrators.
    """
    # Validate password complexity
    validate_password_complexity(user_in.password)

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    if not user_in.date_of_birth:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date of birth is required for student registration"
        )

    # Public registration is strictly locked to student role
    assigned_role = "student"
    
    password_hash = get_password_hash(user_in.password)
    
    user = User(
        email=user_in.email,
        password_hash=password_hash,
        role=assigned_role,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        is_verified=False, # Must be activated via parental consent / school enrollment
        school_id=user_in.school_id
    )
    
    db.add(user)
    db.flush() # Populate user.id
    
    profile = StudentProfile(
        user_id=user.id,
        school_id=user_in.school_id,
        class_id=user_in.class_id,
        board=user_in.board or "CBSE",
        date_of_birth=user_in.date_of_birth,
        interests=["Coding", "Science", "Space"],
        learning_preference=["video", "reading"]
    )
    db.add(profile)
    
    # Link to parent if parent_email is provided via secure invitation
    if user_in.parent_email:
        parent = db.query(User).filter(User.email == user_in.parent_email, User.role == "parent").first()
        if not parent:
            # Generate unique random password hash (never hardcoded Parent123!)
            random_initial_key = secrets.token_urlsafe(32)
            parent = User(
                email=user_in.parent_email,
                password_hash=get_password_hash(random_initial_key),
                role="parent",
                first_name="Guardian",
                last_name="Account",
                is_verified=False, # Must be verified via parent OTP flow
                school_id=user_in.school_id
            )
            db.add(parent)
            db.flush()
            
        # Associate via linked table
        association = parent_student_links.insert().values(
            parent_user_id=parent.id,
            student_user_id=user.id,
            is_verified=False # Verified when parent confirms OTP
        )
        db.execute(association)
        
    db.commit()
    db.refresh(user)

    return user

@router.post("/activate-invite", response_model=Token)
def activate_invitation(req: InviteActivationRequest, db: Session = Depends(get_db)):
    """
    Staff / Guardian Invitation Activation Endpoint:
    Allows an invited teacher, school admin, or guardian to establish their credentials securely.
    """
    # Look up token in Redis
    user_id = redis_client.get(f"invite_token:{req.token}")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    validate_password_complexity(req.password)

    user.password_hash = get_password_hash(req.password)
    if req.first_name:
        user.first_name = req.first_name
    if req.last_name:
        user.last_name = req.last_name
    user.is_verified = True

    db.commit()
    db.refresh(user)

    # Invalidate token
    redis_client.delete(f"invite_token:{req.token}")

    access_token = create_access_token(
        data={"sub": user.email, "role": user.role, "user_id": user.id},
        expires_delta=timedelta(minutes=60)
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_verified": user.is_verified
    }

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "user": user
    }

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    """
    Session Termination Endpoint:
    Revokes the provided JWT access token immediately via Redis session blacklist.
    """
    revoke_token(token, ttl_seconds=3600)
    return {
        "status": "logged_out",
        "message": "Token has been revoked and session terminated successfully."
    }

from app.core.security import RoleChecker

@router.get("/me")
def get_current_user_record(
    current_user: User = Depends(RoleChecker(["student", "teacher", "parent", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Returns the complete profile record of the currently logged-in user.
    """
    prof = None
    if current_user.student_profile:
        sp = current_user.student_profile
        prof = {
            "board": sp.board,
            "grade_level": sp.school_class.grade_level if sp.school_class else 10,
            "section": sp.school_class.section_name if sp.school_class else "A",
            "interests": sp.interests,
            "xp_score": sp.xp_score,
            "streak_count": sp.streak_count,
            "date_of_birth": str(sp.date_of_birth) if sp.date_of_birth else None
        }

    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "is_verified": current_user.is_verified,
        "school": current_user.school.name if current_user.school else "Apex International Academy",
        "created_at": current_user.created_at,
        "student_profile": prof
    }

from pydantic import BaseModel
from app.core.security import verify_google_id_token
from app.models.models import School, SchoolClass

class GoogleLoginRequest(BaseModel):
    id_token: str

@router.post("/google", response_model=Token)
def login_with_google(request: GoogleLoginRequest, db: Session = Depends(get_db)):
    # 1. Verify Google Token
    token_info = verify_google_id_token(request.id_token)
    if not token_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Google ID Token"
        )
        
    email = token_info.get("email")
    google_id = token_info.get("sub")
    first_name = token_info.get("given_name", "Google")
    last_name = token_info.get("family_name", "User")
    
    # 2. Check if user already exists
    user = db.query(User).filter((User.google_id == google_id) | (User.email == email)).first()
    
    if not user:
        # Create new user
        # Determine role from domain, or default to student
        domain = email.split("@")[-1]
        school = db.query(School).filter(School.domain == domain).first()
        
        # Determine role
        # If domain matches school, it's a student at that school.
        # Otherwise, default to student role for new Google signups.
        role = "student"
        
        user = User(
            email=email,
            google_id=google_id,
            password_hash=None, # passwordless
            role=role,
            first_name=first_name,
            last_name=last_name,
            is_verified=(school is not None),
            school_id=school.id if school else None
        )
        db.add(user)
        db.flush()
        
        # Initialize Student Profile
        class_id = None
        if school:
            default_class = db.query(SchoolClass).filter(SchoolClass.school_id == school.id).first()
            if default_class:
                class_id = default_class.id
                
        profile = StudentProfile(
            user_id=user.id,
            school_id=school.id if school else None,
            class_id=class_id,
            board="CBSE",
            date_of_birth=None, # Never invent false DOB; collected upon onboarding
            interests=["Coding", "Science", "Space"],
            learning_preference=["video", "reading"]
        )
        db.add(profile)
        db.commit()
    else:
        # User exists, update Google ID link if empty
        if not user.google_id:
            user.google_id = google_id
            db.commit()
            
    # 3. Generate JWT Token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }
