from datetime import timedelta, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, StudentProfile, parent_student_links
from app.schemas.schemas import UserRegister, UserLogin, Token, UserOut
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Create new User
    password_hash = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        password_hash=password_hash,
        role=user_in.role,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        is_verified=(user_in.role != "student"), # Auto-verify non-students for MVP, students require parent approval
        school_id=user_in.school_id
    )
    
    db.add(user)
    db.flush() # Populate user.id
    
    # Custom logic for Student registration
    if user_in.role == "student":
        if not user_in.date_of_birth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Date of birth is required for students"
            )
            
        profile = StudentProfile(
            user_id=user.id,
            school_id=user_in.school_id,
            class_id=user_in.class_id,
            board=user_in.board or "CBSE",
            date_of_birth=user_in.date_of_birth,
            interests=["Coding", "Science", "Space"], # Default MVP interests
            learning_preference=["video", "reading"]
        )
        db.add(profile)
        
        # Link to parent if parent_email is provided
        if user_in.parent_email:
            # Check if parent already registered
            parent = db.query(User).filter(User.email == user_in.parent_email, User.role == "parent").first()
            if not parent:
                # Mock register a parent user with standard password
                parent_hash = get_password_hash("Parent123!")
                parent = User(
                    email=user_in.parent_email,
                    password_hash=parent_hash,
                    role="parent",
                    first_name="Parent of",
                    last_name=user_in.first_name,
                    is_verified=True
                )
                db.add(parent)
                db.flush()
            
            # Associate via linked table
            association = parent_student_links.insert().values(
                parent_user_id=parent.id,
                student_user_id=user.id,
                is_verified=True # Auto-approve for the MVP
            )
            db.execute(association)
            
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if user.role == "student" and not user.is_verified:
        # Check parent link
        parent_link = db.query(parent_student_links).filter(
            parent_student_links.c.student_user_id == user.id,
            parent_student_links.c.is_verified == True
        ).first()
        if not parent_link:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student account is pending verification by parent"
            )
        else:
            # Auto-verify since parent linked
            user.is_verified = True
            db.commit()
            
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role}
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id
    }
