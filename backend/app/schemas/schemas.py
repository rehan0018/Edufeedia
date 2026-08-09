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
