"""
GitHub Webhook API
Handles incoming GitHub webhook events
"""
import hmac
import hashlib
import json
from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.database import get_db
from app.models.models import ReviewTask, Project
from app.config import settings

router = APIRouter()


def verify_github_signature(payload: bytes, signature: str) -> bool:
    """Verify GitHub webhook HMAC-SHA256 signature"""
    if not settings.GITHUB_WEBHOOK_SECRET:
        return True  # Skip verification if no secret configured

    expected_signature = hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected_signature}", signature)


@router.post("/webhooks/github")
async def github_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle GitHub webhook events"""
    # Get signature from headers
    signature = request.headers.get("X-Hub-Signature-256", "")

    # Read payload
    payload = await request.body()

    # Verify signature
    if not verify_github_signature(payload, signature):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid signature"
        )

    # Parse payload
    event_type = request.headers.get("X-GitHub-Event", "")
    data = json.loads(payload)

    # Handle push event
    if event_type == "push":
        return await handle_push_event(db, data)

    # Handle pull request event
    elif event_type == "pull_request":
        return await handle_pull_request_event(db, data)

    return {"message": "Event received", "type": event_type}


async def handle_push_event(db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle push event"""
    repository = data.get("repository", {})
    repo_name = repository.get("full_name", "")
    commit_sha = data.get("after", "")
    branch = data.get("ref", "").replace("refs/heads/", "")

    # Find project by repository
    project = db.query(Project).filter(Project.github_repo.like(f"%{repo_name}%")).first()

    if not project:
        return {"message": "Project not found, skipped"}

    # Create review task
    task = ReviewTask(
        project_id=project.id,
        commit_sha=commit_sha,
        branch=branch,
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return {
        "message": "Review task created",
        "task_id": task.id,
        "status": status.HTTP_201_CREATED
    }


async def handle_pull_request_event(db: Session, data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle pull request event"""
    action = data.get("action")
    if action not in ["opened", "synchronize", "reopened"]:
        return {"message": "Action not relevant, skipped"}

    repository = data.get("repository", {})
    repo_name = repository.get("full_name", "")
    pr = data.get("pull_request", {})
    pr_number = pr.get("number")
    head_sha = pr.get("head", {}).get("sha", "")
    branch = pr.get("head", {}).get("ref", "")

    # Find project
    project = db.query(Project).filter(Project.github_repo.like(f"%{repo_name}%")).first()

    if not project:
        return {"message": "Project not found, skipped"}

    # Create review task
    task = ReviewTask(
        project_id=project.id,
        commit_sha=head_sha,
        branch=branch,
        pull_request_id=pr_number,
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return {
        "message": "Review task created for PR",
        "task_id": task.id,
        "pr_number": pr_number,
        "status": status.HTTP_201_CREATED
    }


@router.post("/reviews/trigger")
async def trigger_review(
    project_id: int,
    commit_sha: str,
    branch: str = "main",
    pull_request_id: int = None,
    db: Session = Depends(get_db)
):
    """Manually trigger a review"""
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task = ReviewTask(
        project_id=project_id,
        commit_sha=commit_sha,
        branch=branch,
        pull_request_id=pull_request_id,
        status="pending"
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    return {
        "message": "Review task created",
        "task_id": task.id
    }