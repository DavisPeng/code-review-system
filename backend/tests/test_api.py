"""
Test API Endpoints
Run with: pytest tests/test_api.py -v
"""
import pytest
import json
import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models.models import Project, ReviewTask, ReviewIssue


# Temp database
test_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
TEST_DATABASE_URL = f"sqlite:///{test_db.name}"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.unlink(test_db.name)
    except:
        pass


@pytest.fixture
def client(setup_db):
    return TestClient(app)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    yield db
    db.close()


class TestProjectsAPI:
    def test_list_projects(self, client, db_session):
        """Test listing projects"""
        # Create a project
        project = Project(name="test-project", github_repo="https://github.com/test/repo")
        db_session.add(project)
        db_session.commit()
        
        response = client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "test-project"
    
    def test_create_project(self, client):
        """Test creating a project"""
        response = client.post("/api/v1/projects", json={
            "name": "new-project",
            "github_repo": "https://github.com/test/new"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "new-project"
    
    def test_get_project(self, client, db_session):
        """Test getting a project"""
        project = Project(name="get-test", github_repo="https://github.com/test/get")
        db_session.add(project)
        db_session.commit()
        
        response = f"/api/v1/projects/{project.id}"
        resp = client.get(response)
        assert resp.status_code == 200


class TestReviewsAPI:
    def test_list_reviews(self, client, db_session):
        """Test listing reviews"""
        project = Project(name="rev-test", github_repo="https://github.com/test/rev")
        db_session.add(project)
        db_session.commit()
        
        task = ReviewTask(project_id=project.id, commit_sha="abc123", status="pending")
        db_session.add(task)
        db_session.commit()
        
        response = client.get("/api/v1/reviews")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
    
    def test_list_reviews_with_filter(self, client, db_session):
        """Test filtering reviews"""
        project = Project(name="filter-test", github_repo="https://github.com/test/filter")
        db_session.add(project)
        db_session.commit()
        
        task = ReviewTask(project_id=project.id, commit_sha="xyz", status="completed")
        db_session.add(task)
        db_session.commit()
        
        response = client.get("/api/v1/reviews?status=completed")
        assert response.status_code == 200
    
    def test_get_review_detail(self, client, db_session):
        """Test getting review detail"""
        project = Project(name="detail-test", github_repo="https://github.com/test/detail")
        db_session.add(project)
        db_session.commit()
        
        task = ReviewTask(project_id=project.id, commit_sha="def456", status="running")
        db_session.add(task)
        db_session.commit()
        
        response = client.get(f"/api/v1/reviews/{task.id}")
        assert response.status_code == 200
        data = response.json()
        assert "task" in data
    
    def test_get_review_issues(self, client, db_session):
        """Test getting review issues"""
        project = Project(name="issue-test", github_repo="https://github.com/test/issue")
        db_session.add(project)
        db_session.commit()
        
        task = ReviewTask(project_id=project.id, commit_sha="ghi789", status="completed")
        db_session.add(task)
        db_session.commit()
        
        # Add issues
        issue = ReviewIssue(
            task_id=task.id,
            file_path="src/main.cpp",
            line_number=10,
            severity="warning",
            category="style",
            message="Test issue",
            source="ai"
        )
        db_session.add(issue)
        db_session.commit()
        
        response = client.get(f"/api/v1/reviews/{task.id}/issues")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


class TestStatsAPI:
    def test_get_stats(self, client, db_session):
        """Test getting statistics"""
        project = Project(name="stats-test", github_repo="https://github.com/test/stats")
        db_session.add(project)
        db_session.commit()
        
        response = client.get("/api/v1/stats/overview")
        assert response.status_code == 200
        data = response.json()
        assert "total_projects" in data
        assert "total_reviews" in data


class TestRulesAPI:
    def test_list_rules(self, client, db_session):
        """Test listing rules"""
        from app.models.models import ReviewRule
        
        rule = ReviewRule(name="test-rule", category="style", severity="warning")
        db_session.add(rule)
        db_session.commit()
        
        response = client.get("/api/v1/rules")
        assert response.status_code == 200
    
    def test_list_rulesets(self, client, db_session):
        """Test listing rule sets"""
        from app.models.models import RuleSet
        
        ruleset = RuleSet(name="test-ruleset", description="Test")
        db_session.add(ruleset)
        db_session.commit()
        
        response = client.get("/api/v1/rulesets")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])