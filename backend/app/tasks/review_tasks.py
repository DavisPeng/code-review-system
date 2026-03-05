"""
Review Pipeline Tasks
Celery tasks for code review workflow
"""
import traceback
from datetime import datetime
from typing import List
from celery import chain, group
from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.models import ReviewTask, ReviewIssue, ReviewStatus
from app.services.git_service import git_service
from app.services.analyzers import clang_tidy_analyzer, cppcheck_analyzer
from app.services.ai_engine import ai_review_engine
from app.services.notification import notification_service


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def task_fetch_diff(self, task_id: int):
    """
    Step 1: Fetch git diff for the review task
    """
    db = SessionLocal()
    try:
        # Get task
        task = db.query(ReviewTask).filter(ReviewTask.id == task_id).first()
        if not task:
            return {"error": "Task not found"}
        
        # Update status
        task.status = ReviewStatus.RUNNING.value
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Get project
        project = task.project
        
        # Fetch diff
        diff_result = git_service.extract_diff(
            repo_url=project.github_repo,
            commit_sha=task.commit_sha
        )
        
        # Store diff data
        task.diff_data = {
            "commit_sha": diff_result.commit_sha,
            "branch": diff_result.branch,
            "files": [
                {
                    "path": c.file_path,
                    "status": c.status,
                    "additions": c.additions,
                    "deletions": c.deletions,
                    "diff": c.diff[:50000] if c.diff else "",  # Limit diff size
                }
                for c in diff_result.changes
            ],
            "total_files": diff_result.total_files,
            "total_additions": diff_result.total_additions,
            "total_deletions": diff_result.total_deletions,
        }
        db.commit()
        
        return {"status": "success", "task_id": task_id, "files": diff_result.total_files}
    
    except Exception as e:
        db.rollback()
        error_msg = str(e)
        task = db.query(ReviewTask).filter(ReviewTask.id == task_id).first()
        if task:
            task.status = ReviewStatus.FAILED.value
            task.error_message = error_msg
            db.commit()
        return {"error": error_msg}
    finally:
        db.close()


@celery_app.task(bind=True)
def task_static_analysis(self, task_id: int):
    """
    Step 2: Run static analysis (clang-tidy + cppcheck)
    """
    db = SessionLocal()
    try:
        task = db.query(ReviewTask).filter(ReviewTask.id == task_id).first()
        if not task or not task.diff_data:
            return {"error": "Task or diff not found"}
        
        all_issues = []
        
        # Get changed files
        changed_files = [f["path"] for f in task.diff_data.get("files", [])]
        
        # Run clang-tidy if available
        if clang_tidy_analyzer.is_available():
            result = clang_tidy_analyzer.analyze_diff(changed_files)
            all_issues.extend(result.issues)
        
        # Run cppcheck if available
        if cppcheck_analyzer.is_available():
            result = cppcheck_analyzer.analyze_diff(changed_files)
            all_issues.extend(result.issues)
        
        # Save issues to database
        for issue in all_issues:
            db_issue = ReviewIssue(
                task_id=task_id,
                file_path=issue.file_path,
                line_number=issue.line_number,
                severity=issue.severity,
                category=issue.category,
                message=issue.message,
                suggestion=issue.suggestion,
                source=issue.tool
            )
            db.add(db_issue)
        
        # Update counts
        task.static_issues_count = len(all_issues)
        task.issues_count = len(all_issues)
        db.commit()
        
        return {
            "status": "success",
            "task_id": task_id,
            "static_issues": len(all_issues)
        }
    
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def task_ai_review(self, task_id: int):
    """
    Step 3: Run AI review
    """
    db = SessionLocal()
    try:
        task = db.query(ReviewTask).filter(ReviewTask.id == task_id).first()
        if not task or not task.diff_data:
            return {"error": "Task or diff not found"}
        
        # Get project rules
        project = task.project
        rules = list(project.rule_sets[0].rules) if project.rule_sets else []
        
        all_issues = []
        
        # Process each file
        for file_info in task.diff_data.get("files", []):
            diff = file_info.get("diff", "")
            if not diff:
                continue
            
            # Review with AI
            result = ai_review_engine.review(
                diff_content=diff,
                file_path=file_info["path"],
                rules=rules
            )
            
            if result.success:
                for issue in result.issues:
                    db_issue = ReviewIssue(
                        task_id=task_id,
                        file_path=issue.file_path,
                        line_number=issue.line_number,
                        severity=issue.severity,
                        category=issue.category,
                        message=issue.message,
                        suggestion=issue.suggestion,
                        source="ai"
                    )
                    db.add(db_issue)
                    all_issues.append(issue)
        
        # Update counts
        task.ai_issues_count = len(all_issues)
        task.issues_count = task.static_issues_count + task.ai_issues_count
        db.commit()
        
        return {
            "status": "success",
            "task_id": task_id,
            "ai_issues": len(all_issues)
        }
    
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def task_aggregate_results(self, task_id: int):
    """
    Step 4: Aggregate and finalize results
    """
    db = SessionLocal()
    try:
        task = db.query(ReviewTask).filter(ReviewTask.id == task_id).first()
        if not task:
            return {"error": "Task not found"}
        
        # Get final counts
        issues = db.query(ReviewIssue).filter(ReviewIssue.task_id == task_id).all()
        
        task.issues_count = len(issues)
        task.static_issues_count = len([i for i in issues if i.source != "ai"])
        task.ai_issues_count = len([i for i in issues if i.source == "ai"])
        task.status = ReviewStatus.COMPLETED.value
        task.completed_at = datetime.utcnow()
        db.commit()
        
        return {
            "status": "success",
            "task_id": task_id,
            "total_issues": len(issues)
        }
    
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(bind=True)
def task_send_notification(self, task_id: int):
    """
    Step 5: Send notification (optional)
    """
    try:
        notification_service.send_review_complete(task_id)
        return {"status": "success", "notification": "sent"}
    except Exception as e:
        return {"error": str(e)}


def trigger_review(task_id: int):
    """
    Trigger a full review pipeline
    """
    # Define task chain
    pipeline = chain(
        task_fetch_diff.s(task_id),
        task_static_analysis.s(),
        task_ai_review.s(),
        task_aggregate_results.s(),
        task_send_notification.s()
    )
    
    # Execute pipeline
    result = pipeline.apply_async()
    
    return result.id


def trigger_review_group(task_ids: List[int]):
    """
    Trigger reviews for multiple tasks
    """
    jobs = group(trigger_review(task_id) for task_id in task_ids)
    result = jobs.apply_async()
    return result.id