from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Dict, Any
import datetime
from datetime import date

# --- AUTH SCHEMAS ---

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str
    last_name: str
    role: str = Field(default="student", pattern="^(student|parent|teacher|school_admin)$")
    
    # Specific fields for student sign up
    date_of_birth: Optional[datetime.date] = None
    grade_level: Optional[int] = 10
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
    user: Optional['UserOut'] = None

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
    grade_level: Optional[int] = None
    board: Optional[str] = None
    interests: Optional[List[str]] = None
    learning_preference: Optional[List[str]] = None

class StudentOnboardingRequest(BaseModel):
    date_of_birth: datetime.date
    grade_level: Optional[int] = 10
    board: Optional[str] = "CBSE"
    school_id: Optional[str] = None
    interests: Optional[List[str]] = Field(default_factory=list)
    learning_preference: Optional[List[str]] = Field(default_factory=list)

class StudentProfileOut(BaseModel):
    user_id: str
    school_id: Optional[str] = None
    class_id: Optional[str] = None
    grade_level: Optional[int] = 10
    board: str
    date_of_birth: Optional[datetime.date] = None
    onboarding_status: str = "PENDING"
    parental_consent_status: str = "PENDING"
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

class QuestionTeacherOut(BaseModel):
    id: str
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: str
    
    class Config:
        from_attributes = True

class QuizOut(BaseModel):
    id: str
    title: str
    questions: List[QuestionOut]
    
    class Config:
        from_attributes = True

class QuizTeacherOut(BaseModel):
    id: str
    title: str
    questions: List[QuestionTeacherOut]
    
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
    average_mastery_percentage: Optional[float] = None
    total_lessons_completed: int
    at_risk_students_count: int
    students: List[StudentRosterItem]

class QuestionCreate(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None
    difficulty: str = "medium"
    blooms_level: Optional[str] = "Understand"

class QuizCreateRequest(BaseModel):
    title: str
    subject: Optional[str] = "General"
    topic: Optional[str] = "General"
    grade_level: Optional[int] = 10
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

# --- SAFETY PIPELINE SCHEMAS ---

class SafetyCheckRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    target_age_group: Optional[int] = 16 # Default under 18

class SafetyCategoryScore(BaseModel):
    category: str
    score: float # 0.0 to 1.0 probability
    severity: str # LOW, MEDIUM, HIGH

class SafetyReportOut(BaseModel):
    verdict: str # ALLOW, REVIEW, BLOCK
    safety_score: float # 0 to 100
    is_safe: bool
    categories: List[SafetyCategoryScore]
    matched_rules: List[str] = []
    explanation: str

# --- INTERACTION & BEHAVIOR SCHEMAS ---

class InteractionCreate(BaseModel):
    content_item_id: str
    interaction_type: str = Field(..., pattern="^(view|click|watch_time|completed|quiz_completed|bookmark|like|skip)$")
    dwell_time_seconds: Optional[int] = 0

class InteractionOut(BaseModel):
    id: str
    content_item_id: str
    interaction_type: str
    weight: float
    dwell_time_seconds: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# --- RECOMMENDATION ENGINE SCHEMAS ---

class ScoreExplanationOut(BaseModel):
    content_similarity: float
    interest_match: float
    grade_match: float
    behavioral_score: float
    learning_value: float
    content_quality: float
    total_relevance_score: float
    candidate_source: str # 'content_based', 'collaborative', 'spaced_repetition', 'trending'

class RecommendedContentItemOut(BaseModel):
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
    safety_score: float
    edu_score: float
    relevance_percentage: int
    explanation: ScoreExplanationOut

class RecommendationFeedOut(BaseModel):
    student_id: str
    greeting: str
    streak: int
    xp: int
    total_candidates_evaluated: int
    items: List[RecommendedContentItemOut]

# --- AI SOCRATIC TUTOR SCHEMAS ---

class TutorChatMessage(BaseModel):
    role: str # 'user' or 'assistant'
    text: str

class TutorAskRequest(BaseModel):
    content_item_id: Optional[str] = None
    question: str
    conversation_history: Optional[List[TutorChatMessage]] = []

class TutorResponse(BaseModel):
    answer: str
    socratic_cue: str
    follow_up_questions: List[str]
    is_safe: bool = True
    grounding_source: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None
    curriculum_citations: Optional[List[Dict[str, Any]]] = []

# --- AI QUIZ GENERATOR SCHEMAS ---

class QuizGenerateRequest(BaseModel):
    subject: str
    topic: str
    grade_level: Optional[int] = 10
    num_questions: Optional[int] = 3
    content_item_id: Optional[str] = None

class GeneratedQuestionOut(BaseModel):
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: str
    difficulty: str
    blooms_level: str

class QuizGenerateResponse(BaseModel):
    quiz_id: str
    title: str
    subject: str
    topic: str
    total_questions: int
    questions: List[GeneratedQuestionOut]

# --- TOPIC MASTERY & DIAGNOSTIC SCHEMAS ---

class TopicMasteryItem(BaseModel):
    subject: str
    topic: str
    total_attempts: int
    total_score: int
    total_max: int
    accuracy_percentage: float
    is_weak: bool
    status: str

class SubjectMasteryItem(BaseModel):
    subject: str
    mastery_percentage: float
    level: str

class UpcomingRevisionItem(BaseModel):
    topic: str
    subject: str
    interval_days: int
    scheduled_date: str

class TopicMasteryResponse(BaseModel):
    student_id: str
    total_topics_evaluated: int
    weak_topic_count: int
    weak_topics: List[TopicMasteryItem]
    strong_topics: List[TopicMasteryItem]
    all_topics: List[TopicMasteryItem]
    subject_mastery: List[SubjectMasteryItem]
    remedial_schedules_activated: List[str]
    upcoming_revisions: Optional[List[UpcomingRevisionItem]] = None

# --- CONTENT REPORTING SCHEMAS ---

class ContentReportCreate(BaseModel):
    content_item_id: str
    reason: str = Field(..., pattern="^(Unsafe|Incorrect|Not age appropriate|Not educational|Broken|Other)$")
    details: Optional[str] = None

class ContentReportOut(BaseModel):
    id: str
    content_item_id: str
    content_title: Optional[str] = None
    reporter_id: str
    reason: str
    details: Optional[str] = None
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class ContentReportReview(BaseModel):
    report_id: str
    status: str = Field(..., pattern="^(resolved|dismissed)$")
    action_taken: Optional[str] = None

# --- LEARNING HEALTH & TELEMETRY SCHEMAS ---

class LearningHealthOut(BaseModel):
    student_id: str
    learning_health_score: int # 0 to 100
    status_label: str # 'Strong Progress', 'Steady & Consistent', 'Needs Reinforcement'
    mastery_index: float
    streak_days: int
    revision_consistency_rate: float
    weak_topics_count: int
    summary_insight: str

# --- PARENT WEEKLY SUMMARY SCHEMAS ---

class ParentWeeklySummaryOut(BaseModel):
    student_id: str
    student_name: str
    week_start: str
    week_end: str
    lessons_completed: int
    quizzes_taken: int
    average_accuracy: float
    ai_tutor_sessions: int
    mastery_improvement_percentage: float
    topics_needing_revision: List[str]
    safety_incident_count: int
    parent_insight: str

# --- TEACHER INTERVENTION SCHEMAS ---

class TeacherInterventionItem(BaseModel):
    student_id: str
    student_name: str
    class_id: str
    grade_level: int
    section_name: str
    severity: str # 'high', 'medium', 'low'
    reason: str # 'Repeated Low Quiz Accuracy', 'Missed Reviews', 'Struggling with Prerequisite'
    topic: Optional[str] = None
    recommended_action: str

class TeacherInterventionsResponse(BaseModel):
    total_interventions: int
    high_urgency_count: int
    interventions: List[TeacherInterventionItem]


# --- PARENT SCREEN TIME & CONTENT BREAKDOWN SCHEMAS ---

class ScreenTimePolicyUpdate(BaseModel):
    daily_limit_minutes: Optional[int] = Field(None, ge=15, le=360)
    curfew_start_time: Optional[str] = None
    curfew_end_time: Optional[str] = None
    curfew_enabled: Optional[bool] = None
    ai_tutor_max_daily_minutes: Optional[int] = Field(None, ge=5, le=180)
    break_interval_minutes: Optional[int] = Field(None, ge=15, le=120)

class SubjectTimeBreakdown(BaseModel):
    subject: str
    minutes: int
    percentage: float

class ActivityFormatBreakdown(BaseModel):
    activity_type: str
    minutes: int
    percentage: float

class ContentActivityItem(BaseModel):
    id: str
    title: str
    subject: str
    topic: Optional[str] = None
    activity_type: str
    minutes_spent: int
    completed: bool
    timestamp: str

class EarlyActionAlert(BaseModel):
    severity: str # 'info', 'warning', 'positive', 'action_required'
    type: str     # 'fatigue', 'distraction', 'balance', 'limit', 'ai_usage'
    title: str
    description: str
    recommended_action: str

class ScreenTimeAnalyticsOut(BaseModel):
    student_id: str
    student_name: str
    today_screen_time_minutes: int
    weekly_screen_time_minutes: int
    daily_average_minutes: int
    daily_limit_minutes: int
    percent_limit_used: int
    is_over_limit: bool
    curfew_enabled: bool
    curfew_start_time: str
    curfew_end_time: str
    is_curfew_active: bool
    subject_breakdown: List[SubjectTimeBreakdown]
    activity_breakdown: List[ActivityFormatBreakdown]
    recent_activities: List[ContentActivityItem]
    early_action_alerts: List[EarlyActionAlert]
    ai_tutor_minutes_today: int


# ==============================================================================
# EduFeedia Kids & Parent Supervision Architecture Schemas
# ==============================================================================

class ParentRegister(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    parent_pin: Optional[str] = Field(None, min_length=4, max_length=6)

class ParentPinSet(BaseModel):
    pin: str = Field(..., min_length=4, max_length=6)

class ParentPinVerify(BaseModel):
    pin: str

class ParentPinOut(BaseModel):
    verified: bool
    message: str

class ChildProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    preferred_language: Optional[str] = "en"
    secondary_language: Optional[str] = None
    learning_level: Optional[str] = "beginner"
    avatar_mascot: Optional[str] = "space_explorer"
    school_name: Optional[str] = None
    grade_or_class: Optional[str] = None
    interests: Optional[List[str]] = []
    allowed_categories: Optional[List[str]] = [
        "STEM", "Creativity", "World", "Life Skills", "Philosophy & Values", "World Traditions"
    ]
    blocked_categories: Optional[List[str]] = []
    allowed_content_types: Optional[List[str]] = ["video", "story", "activity", "quiz", "game"]
    parent_approved_only: Optional[bool] = False
    daily_limit_minutes: Optional[int] = 45
    curfew_start_time: Optional[str] = "20:00"
    curfew_end_time: Optional[str] = "07:00"
    curfew_enabled: Optional[bool] = True

class ChildProfileUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[date] = None
    age: Optional[int] = None
    preferred_language: Optional[str] = None
    secondary_language: Optional[str] = None
    learning_level: Optional[str] = None
    avatar_mascot: Optional[str] = None
    school_name: Optional[str] = None
    grade_or_class: Optional[str] = None
    interests: Optional[List[str]] = None
    allowed_categories: Optional[List[str]] = None
    blocked_categories: Optional[List[str]] = None
    allowed_content_types: Optional[List[str]] = None
    parent_approved_only: Optional[bool] = None
    daily_limit_minutes: Optional[int] = None
    curfew_start_time: Optional[str] = None
    curfew_end_time: Optional[str] = None
    curfew_enabled: Optional[bool] = None

class ChildProfileOut(BaseModel):
    id: str
    parent_user_id: str
    name: str
    date_of_birth: str
    age: int
    age_band_key: str
    age_band_name: str
    preferred_language: str
    secondary_language: Optional[str] = None
    learning_level: str
    avatar_mascot: str
    interests: List[str]
    allowed_categories: List[str]
    blocked_categories: List[str]
    allowed_content_types: List[str]
    parent_approved_only: bool
    daily_limit_minutes: int
    curfew_start_time: str
    curfew_end_time: str
    curfew_enabled: bool
    is_curfew_active: bool
    today_screen_time_minutes: int
    xp_score: int
    streak_count: int
    stars_count: int
    created_at: str

class ChildControlsUpdate(BaseModel):
    allowed_categories: Optional[List[str]] = None
    blocked_categories: Optional[List[str]] = None
    allowed_content_types: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    learning_level: Optional[str] = None
    preferred_language: Optional[str] = None
    secondary_language: Optional[str] = None
    parent_approved_only: Optional[bool] = None

class ChildScreenTimeUpdate(BaseModel):
    daily_limit_minutes: Optional[int] = Field(None, ge=10, le=180)
    curfew_start_time: Optional[str] = None
    curfew_end_time: Optional[str] = None
    curfew_enabled: Optional[bool] = None

class ChildContentApprovalRequest(BaseModel):
    content_item_id: str
    status: str # 'APPROVED', 'BLOCKED'
    notes: Optional[str] = None

class ChildActivityCreate(BaseModel):
    content_item_id: str
    activity_type: str # 'video', 'story', 'game', 'creative_task', 'experiment', 'quiz'
    dwell_time_seconds: Optional[int] = 0
    completed: Optional[bool] = True
    child_reaction: Optional[str] = None # 'loved', 'good', 'okay', 'confused'

class ChildActivityOut(BaseModel):
    id: str
    child_profile_id: str
    content_item_id: str
    activity_type: str
    dwell_time_seconds: int
    completed: bool
    child_reaction: Optional[str] = None
    stars_earned: int = 1
    created_at: str

class KidsQuizQuestion(BaseModel):
    id: str
    question_text: str
    options: List[str]
    correct_answer: str
    explanation: Optional[str] = None

class KidsQuizSubmit(BaseModel):
    quiz_id: str
    selected_option: str

class KidsQuizResultOut(BaseModel):
    is_correct: bool
    selected_option: str
    correct_answer: str
    positive_feedback: str
    stars_awarded: int
    fun_fact: Optional[str] = None

class KidsAdventureStep(BaseModel):
    step_number: int
    step_type: str # 'watch_cartoon', 'understand_concept', 'interactive_activity', 'mini_quiz', 'earn_badge'
    title: str
    description: str
    icon: str
    status: str # 'completed', 'active', 'locked'
    content_item_id: Optional[str] = None
    duration_label: str

class KidsAdventureOut(BaseModel):
    adventure_id: str
    theme_title: str
    mascot_name: str
    mascot_avatar: str
    greeting: str
    steps: List[KidsAdventureStep]
    total_stars_available: int
    progress_percentage: int

class WhySeeingThisOut(BaseModel):
    content_id: str
    title: str
    category: str
    reasons: List[str]
    age_match: str
    parent_allowed: bool
    learning_balance_note: str

class ChildDashboardOut(BaseModel):
    child_id: str
    child_name: str
    age: int
    avatar_mascot: str
    today_learning_minutes: int
    daily_limit_minutes: int
    percent_used: int
    is_over_limit: bool
    is_curfew_active: bool
    videos_completed: int
    quizzes_completed: int
    activities_completed: int
    stars_earned: int
    current_streak: int
    category_time_breakdown: List[Dict[str, Any]]
    observed_interests: List[Dict[str, Any]]
    recent_activities: List[Dict[str, Any]]
    parent_alerts: List[Dict[str, Any]]

