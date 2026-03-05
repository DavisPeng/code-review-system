"""
Notification API
Endpoints for managing notification configurations
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.models import NotificationConfig

router = APIRouter()


# Pydantic schemas
class NotificationConfigCreate(BaseModel):
    project_id: int
    channel: str = "feishu"
    webhook_url: Optional[str] = None
    notify_on_completed: bool = True
    notify_on_failed: bool = False


class NotificationConfigUpdate(BaseModel):
    channel: Optional[str] = None
    webhook_url: Optional[str] = None
    notify_on_completed: Optional[bool] = None
    notify_on_failed: Optional[bool] = None


class NotificationConfigSchema(BaseModel):
    id: int
    project_id: int
    channel: str
    webhook_url: Optional[str]
    notify_on_completed: bool
    notify_on_failed: bool

    class Config:
        from_attributes = True


@router.post("/notifications/config", response_model=NotificationConfigSchema)
async def create_notification_config(
    config: NotificationConfigCreate,
    db: Session = Depends(get_db)
):
    """Create notification configuration for a project"""
    # Check if config already exists for project
    existing = db.query(NotificationConfig).filter(
        NotificationConfig.project_id == config.project_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Notification config already exists for this project"
        )

    db_config = NotificationConfig(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)

    return db_config


@router.get("/notifications/config/{project_id}", response_model=NotificationConfigSchema)
async def get_notification_config(project_id: int, db: Session = Depends(get_db)):
    """Get notification configuration for a project"""
    config = db.query(NotificationConfig).filter(
        NotificationConfig.project_id == project_id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Notification config not found")

    return config


@router.put("/notifications/config/{project_id}", response_model=NotificationConfigSchema)
async def update_notification_config(
    project_id: int,
    config: NotificationConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update notification configuration"""
    db_config = db.query(NotificationConfig).filter(
        NotificationConfig.project_id == project_id
    ).first()

    if not db_config:
        raise HTTPException(status_code=404, detail="Notification config not found")

    for key, value in config.model_dump(exclude_unset=True).items():
        setattr(db_config, key, value)

    db.commit()
    db.refresh(db_config)

    return db_config


@router.post("/notifications/test")
async def test_notification(
    webhook_url: str,
    channel: str = "feishu"
):
    """Send a test notification"""
    if channel == "feishu":
        # Test Feishu webhook
        import requests

        try:
            response = requests.post(
                webhook_url,
                json={
                    "msg_type": "text",
                    "content": {
                        "text": "🧪 测试消息：AI Code Review System 飞书通知配置成功！"
                    }
                },
                timeout=10
            )

            if response.status_code == 200:
                return {"message": "Test notification sent successfully"}
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to send notification: {response.text}"
                )
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return {"message": "Test notification sent"}


@router.delete("/notifications/config/{project_id}")
async def delete_notification_config(project_id: int, db: Session = Depends(get_db)):
    """Delete notification configuration"""
    db_config = db.query(NotificationConfig).filter(
        NotificationConfig.project_id == project_id
    ).first()

    if not db_config:
        raise HTTPException(status_code=404, detail="Notification config not found")

    db.delete(db_config)
    db.commit()

    return {"message": "Notification config deleted successfully"}