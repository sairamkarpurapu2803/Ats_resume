"""Authentication Endpoints"""

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from datetime import timedelta
import os

router = APIRouter()

class APIKeyRequest(BaseModel):
    """API Key request model"""
    gemini_api_key: str

class APIKeyResponse(BaseModel):
    """API Key response model"""
    message: str
    api_key_masked: str
    expires_in: int

@router.post("/validate-api-key", response_model=APIKeyResponse)
async def validate_api_key(request: APIKeyRequest):
    """Validate and store Gemini API key"""
    if not request.gemini_api_key or len(request.gemini_api_key) < 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid API key format"
        )
    
    # Mask the key for security
    masked_key = request.gemini_api_key[:5] + "*" * (len(request.gemini_api_key) - 10) + request.gemini_api_key[-5:]
    
    # Store in environment (in production, use secure storage)
    os.environ["GEMINI_API_KEY"] = request.gemini_api_key
    
    return APIKeyResponse(
        message="API key validated successfully",
        api_key_masked=masked_key,
        expires_in=3600
    )

@router.get("/api-key-status")
async def check_api_key_status():
    """Check if API key is configured"""
    has_key = "GEMINI_API_KEY" in os.environ
    return {
        "configured": has_key,
        "message": "API key is configured" if has_key else "Please configure API key first"
    }
