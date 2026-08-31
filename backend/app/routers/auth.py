import secrets
import hashlib
import datetime
from datetime import timedelta, date, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.models import User, StudentProfile, parent_student_links, StaffInvitation
from app.schemas.schemas import UserRegister, UserLogin, Token, UserOut
from app.core.security import (
    get_password_hash, verify_password, create_access_token,
    validate_password_complexity, revoke_token, oauth2_scheme, get_current_user
)
from app.core.redis_client import redis_client
from app.core.email_service import email_service
from app.core.age_policy import StudentAgePolicy

router = APIRouter(prefix="/auth", tags=["auth"])

class InviteActivationRequest(BaseModel):
    token: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, request: Request, db: Session = Depends(get_db)):
    """
    Public Registration Endpoint: Strictly restricted to Student accounts only.
    Teachers and School Administrators must be invited by authorized school administrators.
    School affiliation is not trusted from public payload and starts unassigned until verified.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    if not redis_client.check_rate_limit(f"register_ip:{client_ip}", max_requests=10, window_seconds=3600):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later."
        )

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

    # Validate age using canonical StudentAgePolicy (Grades 6–12 / Ages 10–17)
    age_res = StudentAgePolicy.validate_student_age(user_in.date_of_birth)
    if not age_res["is_eligible"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=age_res["reason"]
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
        onboarding_status="PENDING",
        parental_consent_status="PENDING",
        interests=[],
        learning_preference=[]
    )
    db.add(profile)
    
    # Link to parent if parent_email is provided via structured invitation workflow
    if user_in.parent_email:
        from app.models.models import PendingGuardianInvitation
        invitation_token = secrets.token_urlsafe(32)
        invitation = PendingGuardianInvitation(
            student_user_id=user.id,
            guardian_email=user_in.parent_email,
            invitation_token=invitation_token,
            status="pending",
            expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)
        )
        db.add(invitation)
        
        email_service.send_guardian_invitation_email(
            guardian_email=user_in.parent_email,
            student_name=f"{user_in.first_name} {user_in.last_name}",
            invitation_token=invitation_token
        )
        
    db.commit()
    db.refresh(user)

    return user

@router.post("/activate-invite", response_model=Token)
def activate_invitation(req: InviteActivationRequest, db: Session = Depends(get_db)):
    """
    Staff / Guardian Invitation Activation Endpoint:
    Allows an invited teacher, school admin, or guardian to establish their credentials securely.
    """
    from app.models.models import PendingGuardianInvitation
    validate_password_complexity(req.password)

    # 1. Check database-backed PendingGuardianInvitation
    guardian_inv = db.query(PendingGuardianInvitation).filter(
        PendingGuardianInvitation.invitation_token == req.token,
        PendingGuardianInvitation.status == "pending"
    ).first()

    if guardian_inv:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        exp = guardian_inv.expires_at
        if exp and exp.tzinfo is None:
            exp = exp.replace(tzinfo=datetime.timezone.utc)
        if exp and exp < now_utc:
            guardian_inv.status = "expired"
            db.commit()
            raise HTTPException(status_code=400, detail="Guardian invitation has expired. Please request a new invite.")

        parent = db.query(User).filter(User.email == guardian_inv.guardian_email).first()
        if not parent:
            parent = User(
                email=guardian_inv.guardian_email,
                password_hash=get_password_hash(req.password),
                role="parent",
                first_name=req.first_name or "Guardian",
                last_name=req.last_name or "Parent",
                is_verified=False,
                account_status="ACTIVE"
            )
            db.add(parent)
            db.flush()
        else:
            # Protect existing parent accounts: do NOT overwrite their password
            if req.first_name and not parent.first_name:
                parent.first_name = req.first_name
            if req.last_name and not parent.last_name:
                parent.last_name = req.last_name

        # Link parent to student if not linked
        existing_link = db.execute(
            parent_student_links.select().where(
                (parent_student_links.c.parent_user_id == parent.id) &
                (parent_student_links.c.student_user_id == guardian_inv.student_user_id)
            )
        ).first()

        if not existing_link:
            db.execute(
                parent_student_links.insert().values(
                    parent_user_id=parent.id,
                    student_user_id=guardian_inv.student_user_id,
                    is_verified=False
                )
            )

        guardian_inv.status = "accepted"
        db.commit()
        db.refresh(parent)

        access_token = create_access_token(
            data={"sub": parent.email, "role": parent.role}
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "role": parent.role,
            "user_id": parent.id
        }

    # 2. Check Authoritative Staff Invitation Record via SHA-256 token hash
    token_hash = hashlib.sha256(req.token.encode("utf-8")).hexdigest()
    invitation = db.query(StaffInvitation).filter(StaffInvitation.token_hash == token_hash).first()
    
    user_id = None
    if invitation:
        if invitation.status == "REVOKED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This invitation has been revoked by an administrator."
            )
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        exp = invitation.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=datetime.timezone.utc)
        if exp < now_utc:
            invitation.status = "EXPIRED"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation token has expired."
            )
        if invitation.status != "PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation token has already been used or is inactive."
            )
        user_id = invitation.user_id
    else:
        # Fallback to Redis cache for legacy tokens
        user_id = redis_client.get(f"invite_token:{req.token}")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invitation token."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    user.password_hash = get_password_hash(req.password)
    if req.first_name:
        user.first_name = req.first_name
    if req.last_name:
        user.last_name = req.last_name
    user.is_verified = True
    user.account_status = "ACTIVE"

    if invitation:
        invitation.status = "ACCEPTED"
        invitation.accepted_at = datetime.datetime.now(datetime.timezone.utc)

    db.commit()
    db.refresh(user)

    # Invalidate token in Redis
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
def login(credentials: UserLogin, request: Request, db: Session = Depends(get_db)):
    email_key = credentials.email.lower().strip()
    rate_key = f"login_rate_limit:{email_key}"
    attempts = redis_client.get(rate_key)
    if attempts and int(attempts) >= 8:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Account temporarily locked for 15 minutes."
        )

    user = db.query(User).filter(User.email == credentials.email).first()
    if not user:
        redis_client.set(rate_key, str(int(attempts or 0) + 1), ex=900)
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
        redis_client.set(rate_key, str(int(attempts or 0) + 1), ex=900)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Clear rate limit counter upon successful credentials verification
    redis_client.delete(rate_key)

    # Check staff verification status
    if user.role in ["teacher", "school_admin"] and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff account activation is pending. Please activate your account via the invitation link sent to your email."
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

@router.post("/forgot-password")
def forgot_password(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Dispatches a 15-minute password reset token to the requested email address.
    Fails silently to prevent user account enumeration attacks.
    """
    email_clean = req.email.lower().strip()
    rate_key = f"forgot_pwd_rate:{email_clean}"
    if not redis_client.check_rate_limit(rate_key, max_requests=5, window_seconds=900):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please try again in 15 minutes."
        )

    user = db.query(User).filter(User.email == email_clean).first()
    if user:
        reset_token = secrets.token_urlsafe(32)
        redis_client.set(f"pwd_reset:{reset_token}", user.id, ex=900)
        token_hash = hashlib.sha256(reset_token.encode("utf-8")).hexdigest()
        redis_client.set(f"pwd_reset_hash:{token_hash}", user.id, ex=900)

        email_service.send_password_reset_email(
            recipient_email=user.email,
            recipient_name=user.first_name or "Student/Educator",
            reset_token=reset_token
        )

    return {
        "status": "request_processed",
        "message": "If an account with this email exists, a password reset link has been dispatched to your inbox."
    }

@router.post("/reset-password")
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Redeems a valid password reset token and updates the user's password.
    """
    validate_password_complexity(req.new_password)

    user_id = redis_client.get(f"pwd_reset:{req.token}")
    if not user_id:
        token_hash = hashlib.sha256(req.token.encode("utf-8")).hexdigest()
        user_id = redis_client.get(f"pwd_reset_hash:{token_hash}")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found.")

    user.password_hash = get_password_hash(req.new_password)
    db.commit()

    redis_client.delete(f"pwd_reset:{req.token}")
    token_hash = hashlib.sha256(req.token.encode("utf-8")).hexdigest()
    redis_client.delete(f"pwd_reset_hash:{token_hash}")
    redis_client.delete(f"login_rate_limit:{user.email.lower()}")

    return {
        "status": "password_reset_success",
        "message": "Your password has been successfully reset. Please log in with your new password."
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
