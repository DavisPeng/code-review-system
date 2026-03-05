"""
Statistics API
Endpoints for system statistics and metrics
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.models import ReviewTask, ReviewIssue, Project

router = APIRouter()


@router.get("/stats/overview")
async def get_overview_stats(db: Session = Depends(get_db)):
    """Get overview statistics"""

    # Total projects
    total_projects = db.query(Project).count()

    # Total reviews
    total_reviews = db.query(ReviewTask).count()

    # Reviews by status
    status_counts = db.query(
        ReviewTask.status,
        func.count(ReviewTask.id)
    ).group_by(ReviewTask.status).all()

    status_dict = {status: count for status, count in status_counts}

    # Issues by severity
    severity_counts = db.query(
        ReviewIssue.severity,
        func.count(ReviewIssue.id)
    ).group_by(ReviewIssue.severity).all()

    severity_dict = {severity: count for severity, count in severity_counts}

    # Recent reviews (last 7 days)
    recent_reviews = db.query(ReviewTask).order_by(
        ReviewTask.created_at.desc()
    ).limit(10).all()

    # Issues by category
    category_counts = db.query(
        ReviewIssue.category,
        func.count(ReviewIssue.id)
    ).group_by(ReviewIssue.category).all()

    category_dict = {category: count for category, count in category_counts}

    return {
        "total_projects": total_projects,
        "total_reviews": total_reviews,
        "reviews_by_status": status_dict,
        "issues_by_severity": severity_dict,
        "issues_by_category": category_dict,
        "recent_reviews": [
            {
                "id": r.id,
                "commit_sha": r.commit_sha[:8],
                "status": r.status,
                "issues_count": r.issues_count,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in recent_reviews
        ]
    }