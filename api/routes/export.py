"""Resume Export Endpoints"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import uuid
from datetime import datetime

from services.resume_optimizer import (
    optimize_resume,
    generate_docx_resume,
    generate_pdf_resume,
    generate_plaintext_resume,
    generate_markdown_resume
)
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

class ExportRequest(BaseModel):
    """Resume export request model"""
    resume_data: dict
    job_description: str
    format: str  # "pdf", "docx", "plaintext", "markdown"
    theme: Optional[str] = "professional"  # "professional", "modern", "minimalist"

@router.post("/optimize")
async def optimize_resume_endpoint(
    resume_data: dict,
    job_description: str,
    preserve_format: bool = True
):
    """
    One-click resume optimization
    
    Rewrites resume for maximum ATS compatibility while:
    - Maintaining original format/style
    - Adding quantifiable metrics
    - Reorganizing by job relevance
    - Keeping resume length optimal
    """
    try:
        logger.info("Optimizing resume...")
        
        optimized = optimize_resume(
            resume_data,
            job_description,
            preserve_format=preserve_format
        )
        
        return {
            "status": "success",
            "optimized_resume": optimized,
            "changes_made": {
                "bullets_rewritten": True,
                "metrics_added": True,
                "format_preserved": preserve_format
            }
        }
    
    except Exception as e:
        logger.error(f"Resume optimization failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Optimization failed: {str(e)}"
        )

@router.post("/export")
async def export_resume(
    request: ExportRequest,
    background_tasks: BackgroundTasks
):
    """
    Export optimized resume in requested format
    
    Supported formats:
    - PDF: Professional PDF with customizable themes
    - DOCX: Editable Word document
    - plaintext: ATS-compatible plain text
    - markdown: GitHub/portfolio markdown
    """
    try:
        logger.info(f"Exporting resume as {request.format}...")
        
        # Optimize resume
        optimized_resume = optimize_resume(
            request.resume_data,
            request.job_description
        )
        
        # Generate unique filename
        export_dir = "exports"
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"optimized_resume_{timestamp}"
        
        # Export in requested format
        if request.format.lower() == "pdf":
            output_path = os.path.join(export_dir, f"{base_name}.pdf")
            generate_pdf_resume(
                optimized_resume,
                output_path,
                theme=request.theme
            )
            file_type = "application/pdf"
        
        elif request.format.lower() == "docx":
            output_path = os.path.join(export_dir, f"{base_name}.docx")
            generate_docx_resume(
                optimized_resume,
                output_path
            )
            file_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        
        elif request.format.lower() == "plaintext":
            output_path = os.path.join(export_dir, f"{base_name}.txt")
            generate_plaintext_resume(
                optimized_resume,
                output_path
            )
            file_type = "text/plain"
        
        elif request.format.lower() == "markdown":
            output_path = os.path.join(export_dir, f"{base_name}.md")
            generate_markdown_resume(
                optimized_resume,
                output_path
            )
            file_type = "text/markdown"
        
        else:
            raise ValueError(f"Unsupported format: {request.format}")
        
        # Schedule cleanup (keep for 24 hours)
        background_tasks.add_task(cleanup_export, output_path, delay=86400)
        
        logger.info(f"Resume exported successfully: {output_path}")
        
        return FileResponse(
            path=output_path,
            filename=os.path.basename(output_path),
            media_type=file_type
        )
    
    except Exception as e:
        logger.error(f"Resume export failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )

@router.post("/batch-export")
async def batch_export_resume(
    resume_data: dict,
    job_description: str,
    formats: list = ["pdf", "docx", "plaintext"]
):
    """
    Export resume in multiple formats at once
    
    Returns URLs for all generated files
    """
    try:
        logger.info(f"Batch exporting resume in {len(formats)} formats...")
        
        optimized_resume = optimize_resume(
            resume_data,
            job_description
        )
        
        export_dir = "exports"
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files = {}
        
        for fmt in formats:
            base_name = f"optimized_resume_{timestamp}"
            
            if fmt == "pdf":
                output_path = os.path.join(export_dir, f"{base_name}.pdf")
                generate_pdf_resume(optimized_resume, output_path)
                files["pdf"] = output_path
            
            elif fmt == "docx":
                output_path = os.path.join(export_dir, f"{base_name}.docx")
                generate_docx_resume(optimized_resume, output_path)
                files["docx"] = output_path
            
            elif fmt == "plaintext":
                output_path = os.path.join(export_dir, f"{base_name}.txt")
                generate_plaintext_resume(optimized_resume, output_path)
                files["plaintext"] = output_path
            
            elif fmt == "markdown":
                output_path = os.path.join(export_dir, f"{base_name}.md")
                generate_markdown_resume(optimized_resume, output_path)
                files["markdown"] = output_path
        
        return {
            "status": "success",
            "files": files,
            "message": f"Resume exported in {len(files)} formats"
        }
    
    except Exception as e:
        logger.error(f"Batch export failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch export failed: {str(e)}"
        )

def cleanup_export(file_path: str, delay: int = 0):
    """Background task to clean up exported file after delay"""
    import time
    import asyncio
    
    if delay > 0:
        time.sleep(delay)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up export: {file_path}")
    except Exception as e:
        logger.error(f"Cleanup failed for {file_path}: {str(e)}")
