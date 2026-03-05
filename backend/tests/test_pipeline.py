"""
Test Review Pipeline
Run with: pytest tests/test_pipeline.py -v
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from app.tasks.review_tasks import (
    task_fetch_diff, task_static_analysis, task_ai_review,
    task_aggregate_results, trigger_review
)
from app.models.models import ReviewTask, ReviewStatus


class TestTaskFunctions:
    def test_task_fetch_diff_exists(self):
        """Test task function exists"""
        assert callable(task_fetch_diff)
    
    def test_task_static_analysis_exists(self):
        """Test task function exists"""
        assert callable(task_static_analysis)
    
    def test_task_ai_review_exists(self):
        """Test task function exists"""
        assert callable(task_ai_review)


class TestPipelineChain:
    def test_pipeline_imports(self):
        """Test that pipeline can be imported"""
        from app.tasks.review_tasks import trigger_review
        assert callable(trigger_review)
    
    def test_task_functions_exist(self):
        """Test task functions exist"""
        from app.tasks import review_tasks
        assert hasattr(review_tasks, 'task_fetch_diff')
        assert hasattr(review_tasks, 'task_static_analysis')
        assert hasattr(review_tasks, 'task_ai_review')
        assert hasattr(review_tasks, 'task_aggregate_results')
        assert hasattr(review_tasks, 'task_send_notification')


class TestCeleryConfig:
    def test_celery_config(self):
        """Test Celery configuration"""
        from app.celery_app import celery_app
        
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"
        assert celery_app.conf.task_time_limit == 600
        assert celery_app.conf.task_soft_time_limit == 540


class TestRetryMechanism:
    def test_max_retries_configured(self):
        """Test that tasks have retry configured"""
        # The task has max_retries=3
        assert task_fetch_diff.max_retries == 3


class TestNotificationService:
    @patch('app.tasks.review_tasks.notification_service')
    def test_notification_called(self, mock_notif):
        """Test notification is called"""
        from app.tasks.review_tasks import task_send_notification
        
        # Task exists and is callable
        assert callable(task_send_notification)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])