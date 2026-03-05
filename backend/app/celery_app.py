"""
Celery Application Configuration
"""
from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "code_review_system",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.review_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max
    task_soft_time_limit=540,  # 9 minutes soft limit
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Import tasks to register them
from app.tasks import review_tasks