"""
Notification Service
Handles sending notifications (Feishu, etc.)
"""
import requests
from typing import Optional
from app.config import settings
from app.database import SessionLocal
from app.models.models import ReviewTask, NotificationConfig


class NotificationService:
    """Base notification service"""
    
    def send(self, webhook_url: str, message: dict) -> bool:
        """Send notification"""
        raise NotImplementedError


class FeishuNotifier(NotificationService):
    """Feishu webhook notifier"""
    
    def send(self, webhook_url: str, message: dict) -> bool:
        """Send Feishu notification"""
        try:
            response = requests.post(webhook_url, json=message, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Feishu notification: {e}")
            return False
    
    def send_review_complete(self, webhook_url: str, task: ReviewTask):
        """Send review completion notification"""
        # Build card message
        card = {
            "header": {
                "title": f"✅ Code Review Completed",
                "template": "green"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**Commit:** {task.commit_sha[:8]}\n"
                                   f"**Branch:** {task.branch}\n"
                                   f"**Issues:** {task.issues_count} total "
                                   f"({task.static_issues_count} static, {task.ai_issues_count} AI)",
                        "tag": "markdown"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {"content": "View Details", "tag": "plain_text"},
                            "url": f"{settings.FRONTEND_URL or 'http://localhost:5173'}/reviews/{task.id}",
                            "type": "primary"
                        }
                    ]
                }
            ]
        }
        
        message = {"msg_type": "interactive", "card": card}
        return self.send(webhook_url, message)


# Singleton instance
notification_service = FeishuNotifier()


# Helper functions
def send_review_complete(task_id: int):
    """Send notification for completed review"""
    db = SessionLocal()
    try:
        task = db.query(ReviewTask).filter(ReviewTask.id == task_id).first()
        if not task:
            return
        
        # Get notification config
        config = db.query(NotificationConfig).filter(
            NotificationConfig.project_id == task.project_id
        ).first()
        
        if not config or not config.webhook_url:
            return
        
        # Send notification
        if config.channel == "feishu":
            notification_service.send_review_complete(config.webhook_url, task)
    
    finally:
        db.close()


def send_test_notification(webhook_url: str, channel: str = "feishu") -> bool:
    """Send test notification"""
    if channel == "feishu":
        message = {
            "msg_type": "text",
            "content": {"text": "🧪 Test: AI Code Review System notification configured!"}
        }
        return notification_service.send(webhook_url, message)
    
    return False