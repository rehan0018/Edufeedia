import datetime
from sqlalchemy.orm import Session
from app.models.models import ContentItem, StudentProgress, SpacedRepetitionSchedule, StudentProfile

def calculate_sm2(quality: int, prev_interval: int, prev_repetition: int, prev_easiness_factor: float):
    """
    SuperMemo-2 (SM-2) Spaced Repetition Algorithm
    quality: 0 (worst) to 5 (best)
    prev_interval: previous interval in days
    prev_repetition: previous repetition count
    prev_easiness_factor: previous easiness factor
    Returns: (new_interval, new_repetition, new_easiness_factor)
    """
    # Clip quality to [0, 5]
    quality = max(0, min(5, quality))
    
    # Calculate new easiness factor
    ef = float(prev_easiness_factor) + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if ef < 1.3:
        ef = 1.3
        
    if quality < 3:
        # Quality is too low, start review cycle from beginning
        repetition = 0
        interval = 1
    else:
        repetition = prev_repetition + 1
        if repetition == 1:
            interval = 1
        elif repetition == 2:
            interval = 6
        else:
            interval = int(round(prev_interval * ef))
            
    return interval, repetition, ef

def generate_daily_feed(db: Session, student_id: str) -> list:
    """
    Generates a personalized daily learning feed for a student.
    Selects 3 syllabus content items + 1 spaced repetition review item.
    """
    # 1. Fetch student profile
    profile = db.query(StudentProfile).filter(StudentProfile.user_id == student_id).first()
    if not profile:
        return []
        
    # 2. Get completed content IDs to avoid recommending already finished items
    completed_progress = db.query(StudentProgress).filter(
        StudentProgress.student_user_id == student_id,
        StudentProgress.progress_percentage == 100
    ).all()
    completed_ids = [p.content_item_id for p in completed_progress]
    
    feed = []
    
    # 3. Choose 1 item from each of the student's interests / subjects (max 3 items)
    subjects_to_query = profile.interests if profile.interests else ["Mathematics", "Science", "Coding"]
    
    # Cap subject queries to prevent huge feeds
    for subject in subjects_to_query[:3]:
        item = db.query(ContentItem).filter(
            ContentItem.grade_level == (profile.school_class.grade_level if profile.school_class else 10),
            ContentItem.board == profile.board,
            ContentItem.subject.ilike(f"%{subject}%"),
            ContentItem.is_approved == True,
            ~ContentItem.id.in_(completed_ids) if completed_ids else True
        ).first()
        
        if item:
            feed.append(item)
            
    # If not enough items, pad with general approved content matching grade
    if len(feed) < 3:
        already_in_feed = [item.id for item in feed]
        padding_items = db.query(ContentItem).filter(
            ContentItem.is_approved == True,
            ~ContentItem.id.in_(completed_ids) if completed_ids else True,
            ~ContentItem.id.in_(already_in_feed) if already_in_feed else True
        ).limit(3 - len(feed)).all()
        feed.extend(padding_items)
        
    # 4. Fetch spaced repetition review items due today
    today = datetime.date.today()
    due_schedule = db.query(SpacedRepetitionSchedule).filter(
        SpacedRepetitionSchedule.student_user_id == student_id,
        SpacedRepetitionSchedule.next_review_date <= today
    ).first()
    
    if due_schedule:
        # Find a content item matching the review topic
        review_item = db.query(ContentItem).filter(
            ContentItem.subject.ilike(f"%{due_schedule.subject}%"),
            ContentItem.topic.ilike(f"%{due_schedule.topic}%"),
            ContentItem.is_approved == True
        ).first()
        if review_item and review_item not in feed:
            feed.append(review_item)
            
    return feed
