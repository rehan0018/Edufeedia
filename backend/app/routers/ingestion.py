from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.database import get_db
from app.models.models import User, ContentItem
from app.core.security import RoleChecker
from app.ingestion.pipeline import ContentIngestionPipeline

router = APIRouter(prefix="/content/ingestion", tags=["ingestion"])

class IngestRequest(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None
    board: Optional[str] = "CBSE"
    content_type: Optional[str] = "video"

class ReviewActionRequest(BaseModel):
    action: str # "approve" or "reject"
    moderator_notes: Optional[str] = None

@router.post("/submit", status_code=status.HTTP_201_CREATED)
def submit_url_for_ingestion(
    request: IngestRequest,
    current_user: User = Depends(RoleChecker(["teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Submits an educational URL through the automated verification,
    metadata extraction, safety audit, and staging pipeline.
    """
    result = ContentIngestionPipeline.ingest_url(
        db=db,
        url=request.url,
        title=request.title,
        description=request.description,
        submitted_by_user=current_user,
        board=request.board or "CBSE",
        content_type=request.content_type or "video"
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result["reason"]
        )

    return result

@router.get("/pending", response_model=List[Dict[str, Any]])
def get_pending_review_queue(
    current_user: User = Depends(RoleChecker(["teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Returns the list of content items awaiting human moderator approval.
    """
    pending = db.query(ContentItem).filter(ContentItem.is_approved == False).all()
    return [
        {
            "id": item.id,
            "title": item.title,
            "description": item.description,
            "source_url": item.source_url,
            "source_platform": item.source_platform,
            "subject": item.subject,
            "topic": item.topic,
            "grade_level": item.grade_level,
            "board": item.board,
            "safety_score": item.safety_score,
            "edu_score": item.edu_score,
            "created_at": item.created_at.isoformat() if item.created_at else None
        }
        for item in pending
    ]

@router.post("/{content_id}/review")
def review_staged_content(
    content_id: str,
    review: ReviewActionRequest,
    current_user: User = Depends(RoleChecker(["teacher", "school_admin"])),
    db: Session = Depends(get_db)
):
    """
    Approves or rejects a staged content item.
    """
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Content item not found")

    if review.action.lower() == "approve":
        item.is_approved = True
        db.commit()

        try:
            from app.core.excel_exporter import sync_database_to_excel
            sync_database_to_excel(db)
        except Exception as e:
            print(f"[Excel Sync Warning]: {e}")

        return {"status": "approved", "content_id": item.id, "message": "Content successfully approved and published to student feed."}
    elif review.action.lower() == "reject":
        db.delete(item)
        db.commit()

        try:
            from app.core.excel_exporter import sync_database_to_excel
            sync_database_to_excel(db)
        except Exception as e:
            print(f"[Excel Sync Warning]: {e}")

        return {"status": "rejected", "content_id": content_id, "message": "Content item rejected and removed from staging."}
    else:
        raise HTTPException(status_code=400, detail="Action must be 'approve' or 'reject'.")
