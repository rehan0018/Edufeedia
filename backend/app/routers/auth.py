import secrets
import datetime
from datetime import timedelta, date
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.models import User, StudentProfile, parent_student_links
from app.schemas.schemas import UserRegister, UserLogin, Token, UserOut
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    validate_password_complexity, revoke_token, oauth2_scheme, get_current_user
)
from app.core.redis_client import redis_client
from app.core.email_service import email_service

router = APIRouter(prefix="/auth", tags=["auth"])

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
    School affiliation is not trusted from public payload and starts unassigned until verified.
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

    # Validate age is strictly within the K-12 student range: 10 to 17
    today = datetime.date.today()
    dob = user_in.date_of_birth
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 10 or age >= 18:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student age {age} not supported. Edufeedia is designed specifically for students aged 10 to 17."
        )

    # Public registration is strictly locked to student role
    assigned_role = "student"
    
    password_hash = get_password_hash(user_in.password)
    
    # Public registrations start with no trusted school binding until verified
    user = User(
        email=user_in.email,
        password_hash=password_hash,
        role=assigned_role,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        is_verified=False, # Must be activated via parental consent / school enrollment
        school_id=None,
        account_status="ACTIVE"
    )
    
    db.add(user)
    db.flush() # Populate user.id
    
    profile = StudentProfile(
        user_id=user.id,
        school_id=None,
        class_id=None,
        grade_level=user_in.grade_level or 10,
        board=user_in.board or "CBSE",
        date_of_birth=user_in.date_of_birth,
        onboarding_status="COMPLETED",
        parental_consent_status="PENDING",
        interests=[],
        learning_preference=[]
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

    # Issue JWT token
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please use Google sign-in for this account.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.account_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active."
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
def logout_user(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    """
    Terminates active session and blacklists the current JWT token in Redis.
    """
    revoke_token(token, ttl_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    return {
        "status": "success",
        "message": f"Session for {current_user.email} successfully terminated and token revoked."
    }

@router.get("/me", response_model=Dict[str, Any])
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns authenticated user profile details.
    """
    prof = None
    if current_user.student_profile:
        sp = current_user.student_profile
        effective_grade = sp.school_class.grade_level if sp.school_class else sp.grade_level
        prof = {
            "board": sp.board,
            "grade_level": effective_grade,
            "section": sp.school_class.section_name if sp.school_class else None,
            "interests": sp.interests or [],
            "learning_preference": sp.learning_preference or [],
            "onboarding_status": sp.onboarding_status or "PENDING",
            "parental_consent_status": sp.parental_consent_status or "PENDING",
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
        "school": current_user.school.name if current_user.school else None,
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

    # 2. Check verified email claim
    email_verified = token_info.get("email_verified")
    if email_verified is not None and str(email_verified).lower() not in ["true", "1"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email is not verified."
        )
        
    email = token_info.get("email")
    google_id = token_info.get("sub")
    first_name = token_info.get("given_name", "Google")
    last_name = token_info.get("family_name", "User")
    
    # 3. Check if user already exists
    user = db.query(User).filter((User.google_id == google_id) | (User.email == email)).first()
    
    if not user:
        # Create new user - start with unverified school binding
        role = "student"
        
        user = User(
            email=email,
            google_id=google_id,
            password_hash=None, # passwordless
            role=role,
            first_name=first_name,
            last_name=last_name,
            is_verified=False,
            school_id=None,
            account_status="ACTIVE"
        )
        db.add(user)
        db.flush()
        
        # Initialize Student Profile in PENDING onboarding state
        profile = StudentProfile(
            user_id=user.id,
            school_id=None,
            class_id=None,
            board="CBSE",
            date_of_birth=None, # Nullable for incomplete onboarding
            onboarding_status="PENDING",
            parental_consent_status="PENDING",
            interests=[],
            learning_preference=[]
        )
        db.add(profile)
        db.commit()
    else:
        if user.account_status != "ACTIVE":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is not active."
            )
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
