"""FastAPI ATS Resume Optimizer - Main Application Entry Point"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from api.routes import auth, resume, analysis, export, health
from utils.logger import setup_logger

load_dotenv()
logger = setup_logger(__name__)

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 ATS Resume Optimizer starting up...")
    from utils.workspace import init_workspace
    init_workspace()
    yield
    # Shutdown
    logger.info("🛑 ATS Resume Optimizer shutting down...")

app = FastAPI(
    title="ATS Resume Optimizer API",
    description="AI-powered resume optimization for ATS compatibility",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(resume.router, prefix="/api/v1/resume", tags=["Resume"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])

@app.get("/")
async def root():
    return {
        "message": "ATS Resume Optimizer API v2.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("ENV", "development") == "development"
    )
