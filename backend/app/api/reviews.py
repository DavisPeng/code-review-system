"""
Review API
Endpoints for reviewing and managing review tasks
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.models import ReviewTask, ReviewIssue

router = APIRouter()


# Pydantic schemas
class ReviewTaskCreate(BaseModel):
    project_id: int
    commit_sha: str
    branch: Optional[str] = "main"
    pull_request_id: Optional[int] = None


class ReviewIssueSchema(BaseModel):
    id: int
    task_id: int
    file_path: str
    line_number: Optional[int]
    severity: str
    category: str
    message: str
    suggestion: Optional[str]
    source: str

    class Config:
        from_attributes = True


class ReviewTaskSchema(BaseModel):
    id: int
    project_id: int
    commit_sha: str
    branch: Optional[str]
    pull_request_id: Optional[int]
    status: str
    issues_count: int
    static_issues_count: int
    ai_issues_count: int
    created_at: str

    class Config:
        from_attributes = True


@router.get("/reviews", response_model=List[ReviewTaskSchema])
async def list_reviews(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List review tasks with pagination and filtering"""
    query = db.query(ReviewTask)

    if project_id:
        query = query.filter(ReviewTask.project_id == project_id)
    if status:
        query = query.filter(ReviewTask.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    tasks = query.order_by(ReviewTask.created_at.desc()).offset(offset).limit(page_size).all()

    return tasks


@router.get("/reviews/{task_id}")
async def get_review(task_id: int, db: Session = Depends(get_db)):
    """Get review task details"""
    task = db.query(ReviewTask).filter(ReviewTask.id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="Review task not found")

    issues = db.query(ReviewIssue).filter(ReviewIssue.task_id == task_id).all()

    return {
        "task": task,
        "issues": issues
    }


@router.get("/reviews/{task_id}/issues", response_model=List[ReviewIssueSchema])
async def get_review_issues(
    task_id: int,
    severity: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get issues for a review task"""
    query = db.query(ReviewIssue).filter(ReviewIssue.task_id == task_id)

    if severity:
        query = query.filter(ReviewIssue.severity == severity)
    if category:
        query = query.filter(ReviewIssue.category == category)

    issues = query.order_by(ReviewIssue.line_number).all()

    return issues