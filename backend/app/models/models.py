"""
Database Models
SQLAlchemy models for Code Review System
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ReviewStatus(str, enum.Enum):
    """Review task status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class IssueSeverity(str, enum.Enum):
    """Issue severity level"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUGGESTION = "suggestion"


class IssueCategory(str, enum.Enum):
    """Issue category"""
    CODING_STANDARD = "coding_standard"
    LOGIC_ERROR = "logic_error"
    PERFORMANCE = "performance"
    MEMORY_SAFETY = "memory_safety"
    CONCURRENCY = "concurrency"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"


class Project(Base):
    """Project model"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    github_repo = Column(String(500), nullable=True)
    default_branch = Column(String(100), default="main")
    ai_provider = Column(String(50), default="anthropic")
    ai_model = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    review_tasks = relationship("ReviewTask", back_populates="project")
    rule_sets = relationship("RuleSet", secondary="rule_set_mappings", back_populates="projects")
    notification_config = relationship("NotificationConfig", back_populates="project", uselist=False)


class ReviewTask(Base):
    """Review task model"""
    __tablename__ = "review_tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    commit_sha = Column(String(100), nullable=False)
    branch = Column(String(100), nullable=True)
    pull_request_id = Column(Integer, nullable=True)
    status = Column(String(50), default=ReviewStatus.PENDING.value)
    diff_data = Column(JSON, nullable=True)
    issues_count = Column(Integer, default=0)
    static_issues_count = Column(Integer, default=0)
    ai_issues_count = Column(Integer, default=0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="review_tasks")
    issues = relationship("ReviewIssue", back_populates="task")


class ReviewIssue(Base):
    """Review issue model"""
    __tablename__ = "review_issues"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("review_tasks.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    line_number = Column(Integer, nullable=True)
    severity = Column(String(20), nullable=False)
    category = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=True)
    source = Column(String(50), default="ai")  # ai, clang-tidy, cppcheck
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    task = relationship("ReviewTask", back_populates="issues")


class ReviewRule(Base):
    """Review rule model"""
    __tablename__ = "review_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False)
    severity = Column(String(20), default=IssueSeverity.WARNING.value)
    pattern = Column(Text, nullable=True)  # Regex pattern for static analysis
    prompt_section = Column(Text, nullable=True)  # Additional prompt for AI
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rule_sets = relationship("RuleSet", secondary="rule_set_rule_mappings", back_populates="rules")


class RuleSet(Base):
    """Rule set model"""
    __tablename__ = "rule_sets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rules = relationship("ReviewRule", secondary="rule_set_rule_mappings", back_populates="rule_sets")
    projects = relationship("Project", secondary="rule_set_mappings", back_populates="rule_sets")


class NotificationConfig(Base):
    """Notification configuration model"""
    __tablename__ = "notification_configs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), unique=True)
    channel = Column(String(50), default="feishu")
    webhook_url = Column(Text, nullable=True)
    notify_on_completed = Column(Boolean, default=True)
    notify_on_failed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="notification_config")


# Association tables
from sqlalchemy import Table, Column, ForeignKey

rule_set_mappings = Table(
    'rule_set_mappings',
    Base.metadata,
    Column('project_id', Integer, ForeignKey('projects.id'), primary_key=True),
    Column('ruleset_id', Integer, ForeignKey('rule_sets.id'), primary_key=True)
)

rule_set_rule_mappings = Table(
    'rule_set_rule_mappings',
    Base.metadata,
    Column('ruleset_id', Integer, ForeignKey('rule_sets.id'), primary_key=True),
    Column('rule_id', Integer, ForeignKey('review_rules.id'), primary_key=True)
)