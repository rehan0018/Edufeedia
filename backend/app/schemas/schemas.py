from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
import datetime

# --- AUTH SCHEMAS ---

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str
    last_name: str
    role: str = Field(default="student", pattern="^(student|parent|teacher|school_admin)$")
    
    # Specific fields for student sign up
    date_of_birth: Optional[datetime.date] = None
    board: Optional[str] = "CBSE"
    school_id: Optional[str] = None
    class_id: Optional[str] = None
    parent_email: Optional[EmailStr] = None # For guardian link flow

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

class UserOut(BaseModel):
    id: str
    email: EmailStr
    role: str
    first_name: str
    last_name: str
    is_verified: bool = False
    
    class Config:
        from_attributes = True

# --- PROFILE SCHEMAS ---

class StudentProfileUpdate(BaseModel):
    board: Optional[str] = None
    interests: Optional[List[str]] = None
    learning_preference: Optional[List[str]] = None

class StudentProfileOut(BaseModel):
    user_id: str
    school_id: Optional[str] = None
    class_id: Optional[str] = None
    board: str
    date_of_birth: datetime.date
    xp_score: int
    streak_count: int
    interests: List[str]
    learning_preference: List[str]
    
    class Config:
        from_attributes = True

# --- CONTENT SCHEMAS ---

class ContentItemOut(BaseModel):
    id: str
    title: str
    description: Optional[str]
    source_url: str
    source_platform: str
    embed_code: Optional[str]
    type: str
    board: str
    grade_level: int
    subject: str
    topic: str
    difficulty: str
    duration_minutes: int
    
    class Config:
        from_attributes = True

class ProgressUpdate(BaseModel):
    content_item_id: str
    progress_percentage: int = Field(..., ge=0, le=100)

class ProgressResponse(BaseModel):
    status: str
    completed: bool
    xp_earned: int

# --- QUIZ SCHEMAS ---

class QuestionOut(BaseModel):
    id: str
    question_text: str
    options: List[str]
    difficulty: str
    
    class Config:
        from_attributes = True

class QuizOut(BaseModel):
    id: str
    title: str
    questions: List[QuestionOut]
    
    class Config:
        from_attributes = True

class QuestionAnswerSubmit(BaseModel):
    question_id: str
    selected_answer: str

class QuizSubmit(BaseModel):
    quiz_id: str
    answers: List[QuestionAnswerSubmit]

class QuizAttemptOut(BaseModel):
    id: str
    score: int
    max_score: int
    accuracy_percentage: float
    completed_at: datetime.datetime
    
    class Config:
        from_attributes = True

# --- FLASHCARD SCHEMAS ---

class FlashcardOut(BaseModel):
    id: str
    subject: str
    topic: str
    front_text: str
    back_text: str
    hint: Optional[str] = None
    grade_level: int
    board: str

    class Config:
        from_attributes = True

class FlashcardReviewSubmit(BaseModel):
    flashcard_id: str
    rating: int = Field(..., ge=1, le=4) # 1=Again, 2=Hard, 3=Good, 4=Easy

class FlashcardReviewResponse(BaseModel):
    status: str
    next_interval_days: int
    xp_earned: int
    message: str

# --- TEACHER SCHEMAS ---

class TeacherClassOut(BaseModel):
    class_id: str
    grade_level: int
    section_name: str
    academic_year: str
    subject: str
    student_count: int

class StudentRosterItem(BaseModel):
    student_id: str
    name: str
    email: str
    xp: int
    streak: int
    average_accuracy: float
    lessons_completed: int
    is_at_risk: bool

class ClassAnalyticsOut(BaseModel):
    class_id: str
    grade_level: int
    section_name: str
    total_students: int
    class_average_accuracy: float
    total_lessons_completed: int
    at_risk_students_count: int
    students: List[StudentRosterItem]

class QuestionCreate(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: str = "medium"

class QuizCreateRequest(BaseModel):
    title: str
    content_item_id: Optional[str] = None
    questions: List[QuestionCreate]

class ClassAssignmentCreate(BaseModel):
    class_id: str
    title: str
    content_item_id: Optional[str] = None
    quiz_id: Optional[str] = None
    instructions: Optional[str] = None
    due_date: Optional[datetime.date] = None

class ClassAssignmentOut(BaseModel):
    id: str
    class_id: str
    title: str
    instructions: Optional[str]
    due_date: Optional[datetime.date]
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- GAMIFICATION & BADGE SCHEMAS ---

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    name: str
    xp: int
    streak: int
    level: int
    is_current_user: bool = False

class BadgeOut(BaseModel):
    id: str
    code: str
    name: str
    description: str
    icon: str
    category: str
    xp_bonus: int
    unlocked: bool = False
    unlocked_at: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True

class StudentBadgesResponse(BaseModel):
    total_badges: int
    unlocked_count: int
    level: int
    current_xp: int
    next_level_xp: int
    level_title: str
    badges: List[BadgeOut]
