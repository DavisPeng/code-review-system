"""
Test database models
Run with: pytest tests/test_models.py -v
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.models import Project, ReviewTask, ReviewIssue, ReviewRule, RuleSet, NotificationConfig


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestProject:
    def test_create_project(self, db):
        """Test creating a project"""
        project = Project(
            name="test-project",
            description="Test project",
            github_repo="https://github.com/test/repo",
            default_branch="main",
            ai_provider="anthropic"
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        
        assert project.id is not None
        assert project.name == "test-project"
        assert project.ai_provider == "anthropic"
    
    def test_get_project(self, db):
        """Test retrieving a project"""
        project = Project(name="test-project", github_repo="https://github.com/test/repo")
        db.add(project)
        db.commit()
        
        retrieved = db.query(Project).filter(Project.name == "test-project").first()
        assert retrieved is not None
        assert retrieved.github_repo == "https://github.com/test/repo"


class TestReviewTask:
    def test_create_review_task(self, db):
        """Test creating a review task"""
        project = Project(name="test-project")
        db.add(project)
        db.commit()
        
        task = ReviewTask(
            project_id=project.id,
            commit_sha="abc123",
            branch="main",
            status="pending"
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        assert task.id is not None
        assert task.commit_sha == "abc123"
        assert task.status == "pending"
    
    def test_review_task_relationships(self, db):
        """Test review task relationships"""
        project = Project(name="test-project")
        db.add(project)
        db.commit()
        
        task = ReviewTask(project_id=project.id, commit_sha="abc123", status="pending")
        db.add(task)
        db.commit()
        
        assert task.project.name == "test-project"


class TestReviewRule:
    def test_create_rule(self, db):
        """Test creating a review rule"""
        rule = ReviewRule(
            name="test-rule",
            description="Test rule",
            category="coding_standard",
            severity="warning"
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
        
        assert rule.id is not None
        assert rule.enabled is True
    
    def test_get_rules_by_category(self, db):
        """Test filtering rules by category"""
        rules = [
            ReviewRule(name="rule1", category="memory_safety", severity="error"),
            ReviewRule(name="rule2", category="memory_safety", severity="warning"),
            ReviewRule(name="rule3", category="performance", severity="info"),
        ]
        for r in rules:
            db.add(r)
        db.commit()
        
        memory_rules = db.query(ReviewRule).filter(ReviewRule.category == "memory_safety").all()
        assert len(memory_rules) == 2


class TestRuleSet:
    def test_create_ruleset(self, db):
        """Test creating a rule set"""
        ruleset = RuleSet(
            name="test-ruleset",
            description="Test rule set",
            is_default=True
        )
        db.add(ruleset)
        db.commit()
        db.refresh(ruleset)
        
        assert ruleset.id is not None
        assert ruleset.is_default is True
    
    def test_ruleset_with_rules(self, db):
        """Test adding rules to a ruleset"""
        rule1 = ReviewRule(name="rule1", category="memory_safety", severity="error")
        rule2 = ReviewRule(name="rule2", category="performance", severity="warning")
        db.add_all([rule1, rule2])
        db.commit()
        
        ruleset = RuleSet(name="test-ruleset")
        ruleset.rules.append(rule1)
        ruleset.rules.append(rule2)
        db.add(ruleset)
        db.commit()
        
        assert len(ruleset.rules) == 2


class TestNotificationConfig:
    def test_create_notification_config(self, db):
        """Test creating notification config"""
        project = Project(name="test-project")
        db.add(project)
        db.commit()
        
        config = NotificationConfig(
            project_id=project.id,
            channel="feishu",
            webhook_url="https://test.webhook",
            notify_on_completed=True,
            notify_on_failed=False
        )
        db.add(config)
        db.commit()
        db.refresh(config)
        
        assert config.id is not None
        assert config.channel == "feishu"
        assert config.notify_on_completed is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])