"""
Application Configuration
Loads settings from environment variables and .env file
"""
import os
from typing import List
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings"""

    # App
    APP_NAME: str = "AI Code Review System"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./data.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # GitHub Webhook
    GITHUB_WEBHOOK_SECRET: str = ""

    # AI Engine
    AI_PROVIDER: str = "anthropic"  # anthropic or openai
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-3-opus-20240229"
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # Static Analysis
    CLANG_TIDY_PATH: str = "clang-tidy"
    CPPCHECK_PATH: str = "cppcheck"

    # Feishu Notification
    FEISHU_WEBHOOK_URL: str = ""
    FRONTEND_URL: str = "http://localhost:5173"

    # Git
    GIT_CACHE_DIR: str = "/tmp/code-review-git-cache"
    GIT_MAX_FILE_LINES: int = 5000

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()