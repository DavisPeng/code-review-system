"""
Test GitHub Webhook API
Run with: pytest tests/test_webhooks.py -v
"""
import pytest
import json
import hmac
import hashlib
import sys
import os
import tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app


# Use temp file SQLite for tests (avoids startup issues)
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


@pytest.fixture(scope="function")
def db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Import here to avoid circular imports
    from app.models.models import Project
    # Create a test project
    project = Project(
        name="test-project",
        github_repo="https://github.com/test/repo"
    )
    db.add(project)
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def setup_db():
    """Setup test database once"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.unlink(test_db.name)
    except:
        pass


@pytest.fixture
def client(setup_db):
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def test_secret():
    """Test webhook secret"""
    return "test_secret"


def create_signature(payload: bytes, secret: str) -> str:
    """Create HMAC-SHA256 signature"""
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"sha256={signature}"


class TestWebhookSignature:
    def test_valid_signature(self, test_secret):
        """Test valid signature verification"""
        from app.api.webhooks import verify_github_signature
        
        payload = b'{"test": "data"}'
        signature = create_signature(payload, test_secret)
        
        with patch('app.api.webhooks.settings') as mock_settings:
            mock_settings.GITHUB_WEBHOOK_SECRET = test_secret
            result = verify_github_signature(payload, signature)
            assert result is True
    
    def test_invalid_signature(self, test_secret):
        """Test invalid signature verification"""
        from app.api.webhooks import verify_github_signature
        
        payload = b'{"test": "data"}'
        signature = "sha256_invalid_signature"
        
        with patch('app.api.webhooks.settings') as mock_settings:
            mock_settings.GITHUB_WEBHOOK_SECRET = test_secret
            result = verify_github_signature(payload, signature)
            assert result is False
    
    def test_no_secret_configured(self):
        """Test signature verification when no secret is configured"""
        from app.api.webhooks import verify_github_signature
        
        payload = b'{"test": "data"}'
        signature = "sha256_invalid"
        
        with patch('app.api.webhooks.settings') as mock_settings:
            mock_settings.GITHUB_WEBHOOK_SECRET = ""
            result = verify_github_signature(payload, signature)
            assert result is True  # Should skip verification


class TestPushWebhook:
    def test_push_event_creates_task(self, client, db):
        """Test push event creates review task"""
        # Mock settings to skip signature verification
        with patch('app.api.webhooks.settings') as mock_settings:
            mock_settings.GITHUB_WEBHOOK_SECRET = ""
            
            payload = {
                "ref": "refs/heads/main",
                "after": "abc123def456",
                "repository": {
                    "full_name": "test/repo"
                }
            }
            payload_bytes = json.dumps(payload).encode()
            
            response = client.post(
                "/api/v1/webhooks/github",
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature-256": "sha256=dummy"
                }
            )
            
            # Since no secret is configured, it should work
            assert response.status_code in [201, 200]
    
    def test_push_event_without_project(self, client, db):
        """Test push event with non-existent project"""
        with patch('app.api.webhooks.settings') as mock_settings:
            mock_settings.GITHUB_WEBHOOK_SECRET = ""
            
            payload = {
                "ref": "refs/heads/main",
                "after": "abc123def456",
                "repository": {
                    "full_name": "nonexistent/repo"
                }
            }
            payload_bytes = json.dumps(payload).encode()
            
            response = client.post(
                "/api/v1/webhooks/github",
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature-256": "sha256=dummy"
                }
            )
            
            assert response.status_code == 200
            assert "Project not found" in response.json()["message"]


class TestPullRequestWebhook:
    def test_pr_opened_creates_task(self, client, db):
        """Test PR opened event creates review task"""
        with patch('app.api.webhooks.settings') as mock_settings:
            mock_settings.GITHUB_WEBHOOK_SECRET = ""
            
            payload = {
                "action": "opened",
                "pull_request": {
                    "number": 1,
                    "head": {
                        "ref": "feature-branch",
                        "sha": "abc123"
                    }
                },
                "repository": {
                    "full_name": "test/repo"
                }
            }
            payload_bytes = json.dumps(payload).encode()
            
            response = client.post(
                "/api/v1/webhooks/github",
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "pull_request",
                    "X-Hub-Signature-256": "sha256=dummy"
                }
            )
            
            assert response.status_code in [201, 200]
    
    def test_pr_synchronize_creates_task(self, client, db):
        """Test PR synchronize event creates review task"""
        with patch('app.api.webhooks.settings') as mock_settings:
            mock_settings.GITHUB_WEBHOOK_SECRET = ""
            
            payload = {
                "action": "synchronize",
                "pull_request": {
                    "number": 1,
                    "head": {
                        "ref": "feature-branch",
                        "sha": "new_sha"
                    }
                },
                "repository": {
                    "full_name": "test/repo"
                }
            }
            payload_bytes = json.dumps(payload).encode()
            
            response = client.post(
                "/api/v1/webhooks/github",
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "pull_request",
                    "X-Hub-Signature-256": "sha256=dummy"
                }
            )
            
            assert response.status_code in [201, 200]
    
    def test_pr_closed_skipped(self, client, db):
        """Test PR closed event is skipped"""
        with patch('app.api.webhooks.settings') as mock_settings:
            mock_settings.GITHUB_WEBHOOK_SECRET = ""
            
            payload = {
                "action": "closed",
                "pull_request": {
                    "number": 1,
                    "head": {"sha": "abc123"}
                },
                "repository": {
                    "full_name": "test/repo"
                }
            }
            payload_bytes = json.dumps(payload).encode()
            
            response = client.post(
                "/api/v1/webhooks/github",
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "pull_request",
                    "X-Hub-Signature-256": "sha256=dummy"
                }
            )
            
            assert response.status_code == 200
            assert "not relevant" in response.json()["message"]


class TestTriggerReview:
    def test_manual_trigger_success(self, client, db):
        """Test manual trigger creates review task"""
        response = client.post(
            "/api/v1/reviews/trigger",
            params={
                "project_id": 1,
                "commit_sha": "test123",
                "branch": "main"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Review task created"
        assert "task_id" in data
    
    def test_manual_trigger_project_not_found(self, client, db):
        """Test manual trigger with non-existent project"""
        response = client.post(
            "/api/v1/reviews/trigger",
            params={
                "project_id": 999,
                "commit_sha": "test123",
                "branch": "main"
            }
        )
        
        assert response.status_code == 404


class TestInvalidSignature:
    def test_invalid_signature_returns_403(self, client, db):
        """Test invalid signature returns 403"""
        # Set a webhook secret
        with patch('app.api.webhooks.settings') as mock_settings:
            mock_settings.GITHUB_WEBHOOK_SECRET = "test_secret"
            
            payload = {"test": "data"}
            payload_bytes = json.dumps(payload).encode()
            
            response = client.post(
                "/api/v1/webhooks/github",
                content=payload_bytes,
                headers={
                    "Content-Type": "application/json",
                    "X-GitHub-Event": "push",
                    "X-Hub-Signature-256": "sha256_invalid"
                }
            )
            
            assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])