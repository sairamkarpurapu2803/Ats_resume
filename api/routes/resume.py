"""Resume Upload and Parsing Endpoints"""

from fastapi import APIRouter, UploadFile, File, HTTPException, status, BackgroundTasks
from typing import Optional
import os
import uuid
from datetime import datetime

from services.resume_parser import parse_resume
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

class ResumeUploadResponse:
    """Resume upload response model"""
    pass

@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Upload and parse resume file (PDF/DOCX)
    
    Returns parsed resume structure with metadata
    """
    # Validate file type
    allowed_types = {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported"
        )
    
    # Validate file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 10MB limit"
        )
    
    # Save temporarily
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    file_path = os.path.join(upload_dir, f"{file_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Parse resume
        logger.info(f"Parsing resume: {file.filename}")
        parsed_data = parse_resume(file_path)
        
        # Schedule cleanup
        background_tasks.add_task(cleanup_file, file_path)
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "uploaded_at": datetime.now().isoformat(),
            "parsed_resume": parsed_data,
            "status": "success"
        }
    
    except Exception as e:
        logger.error(f"Resume parsing failed: {str(e)}")
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Resume parsing failed: {str(e)}"
        )

@router.post("/validate")
async def validate_resume(resume_data: dict):
    """
    Validate resume structure and completeness
    
    Returns validation report with scores
    """
    try:
        validation_report = {
            "sections": {},
            "completeness_score": 0,
            "warnings": [],
            "suggestions": []
        }
        
        # Check required sections
        sections = {
            "name": resume_data.get("name"),
            "email": resume_data.get("email"),
            "phone": resume_data.get("phone"),
            "summary": resume_data.get("summary"),
            "skills": resume_data.get("skills", []),
            "experience": resume_data.get("experience", []),
            "education": resume_data.get("education", []),
        }
        
        section_scores = {}
        total_score = 0
        
        for section, value in sections.items():
            if section == "skills":
                score = min(100, len(value) * 10) if value else 0
                section_scores[section] = score
                if len(value) < 5:
                    validation_report["warnings"].append(f"Add more skills (current: {len(value)}, recommended: 10+)")
            elif section == "experience":
                score = min(100, len(value) * 25) if value else 0
                section_scores[section] = score
                if len(value) == 0:
                    validation_report["suggestions"].append("Add professional experience")
            elif section == "education":
                score = 100 if value else 50
                section_scores[section] = score
            elif section in ["summary", "email", "phone", "name"]:
                score = 100 if value else 0
                section_scores[section] = score
            
            total_score += section_scores[section]
        
        validation_report["sections"] = section_scores
        validation_report["completeness_score"] = int(total_score / len(section_scores))
        
        return validation_report
    
    except Exception as e:
        logger.error(f"Resume validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )

def cleanup_file(file_path: str):
    """Background task to clean up uploaded file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up: {file_path}")
    except Exception as e:
        logger.error(f"Cleanup failed for {file_path}: {str(e)}")
