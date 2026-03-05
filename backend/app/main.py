"""
Code Review System - FastAPI Application
Main entry point for the backend API
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import webhooks, reviews, projects, rules, stats, notifications
from app.config import settings
from app.database import engine, Base

# Create FastAPI app
app = FastAPI(
    title="AI Code Review System",
    description="Intelligent code review system for C/C++ projects with AI-powered analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
cors_origins = settings.CORS_ORIGINS.split(",") if isinstance(settings.CORS_ORIGINS, str) else settings.CORS_ORIGINS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    Base.metadata.create_all(bind=engine)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    pass


# Include routers
app.include_router(webhooks.router, prefix="/api/v1", tags=["webhooks"])
app.include_router(reviews.router, prefix="/api/v1", tags=["reviews"])
app.include_router(projects.router, prefix="/api/v1", tags=["projects"])
app.include_router(rules.router, prefix="/api/v1", tags=["rules"])
app.include_router(stats.router, prefix="/api/v1", tags=["stats"])
app.include_router(notifications.router, prefix="/api/v1", tags=["notifications"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "AI Code Review System",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}