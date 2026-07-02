"""Health Check Endpoints"""

from fastapi import APIRouter, status

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "ATS Resume Optimizer is running"
    }

@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check endpoint"""
    return {
        "status": "ready",
        "message": "Service is ready to accept requests"
    }
