"""ATS Analysis Endpoints"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
import json

from services.ats_analyzer import (
    analyze_ats_matching,
    extract_jd_keywords,
    validate_sections,
    detect_missing_skills,
    calculate_ats_score
)
from utils.logger import setup_logger

logger = setup_logger(__name__)
router = APIRouter()

class AnalysisRequest(BaseModel):
    """ATS Analysis request model"""
    resume_data: dict
    job_description: str
    detailed: bool = True

class SkillGapAnalysis(BaseModel):
    """Skill gap analysis model"""
    critical_missing: List[str]
    recommended_skills: List[str]
    skill_gap_percentage: float
    categories: Dict[str, dict]

class ATSScoreReport(BaseModel):
    """ATS score report model"""
    ats_score: int
    match_percentage: int
    matching_keywords: List[str]
    missing_keywords: List[str]
    section_scores: Dict[str, int]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]

@router.post("/analyze", response_model=ATSScoreReport)
async def analyze_resume(
    request: AnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Analyze resume against job description
    
    Returns comprehensive ATS compatibility report:
    - ATS Score (0-100)
    - Keyword matching analysis
    - Missing skills detection
    - Section validation
    - Actionable suggestions
    """
    try:
        logger.info("Starting ATS analysis...")
        
        # Extract JD keywords
        jd_keywords = extract_jd_keywords(request.job_description)
        logger.info(f"Extracted {len(jd_keywords.get('technical_skills', []))} technical skills from JD")
        
        # Analyze matching
        matching_analysis = analyze_ats_matching(
            request.resume_data,
            jd_keywords
        )
        
        # Validate sections
        section_validation = validate_sections(request.resume_data)
        
        # Calculate comprehensive ATS score
        ats_score = calculate_ats_score(
            matching_analysis,
            section_validation
        )
        
        # Generate insights
        strengths = []
        weaknesses = []
        
        if matching_analysis['match_percentage'] > 70:
            strengths.append(f"Strong keyword alignment: {matching_analysis['match_percentage']}% match")
        else:
            weaknesses.append(f"Low keyword alignment: {matching_analysis['match_percentage']}% match")
        
        if section_validation['completeness'] > 80:
            strengths.append("Resume structure is well-organized")
        else:
            weaknesses.append("Several resume sections need improvement")
        
        return ATSScoreReport(
            ats_score=ats_score,
            match_percentage=matching_analysis['match_percentage'],
            matching_keywords=matching_analysis['matched_skills'][:10],
            missing_keywords=matching_analysis['missing_skills'][:10],
            section_scores=section_validation['section_scores'],
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=matching_analysis['suggestions']
        )
    
    except Exception as e:
        logger.error(f"ATS analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

@router.post("/skill-gap", response_model=SkillGapAnalysis)
async def analyze_skill_gap(
    resume_data: dict,
    job_description: str
):
    """
    Detailed skill gap analysis
    
    Returns:
    - Critical missing skills
    - Recommended skills
    - Category-wise breakdown
    - Gap percentage
    """
    try:
        logger.info("Analyzing skill gaps...")
        
        gap_analysis = detect_missing_skills(
            resume_data,
            job_description
        )
        
        return SkillGapAnalysis(
            critical_missing=gap_analysis['critical_missing'],
            recommended_skills=gap_analysis['recommended'],
            skill_gap_percentage=gap_analysis['gap_percentage'],
            categories=gap_analysis['categories']
        )
    
    except Exception as e:
        logger.error(f"Skill gap analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Skill gap analysis failed: {str(e)}"
        )

@router.post("/section-validation")
async def validate_sections_endpoint(resume_data: dict):
    """
    Validate all resume sections
    
    Returns:
    - Section scores
    - Missing sections
    - Quality recommendations
    """
    try:
        validation_results = validate_sections(resume_data)
        return validation_results
    
    except Exception as e:
        logger.error(f"Section validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Section validation failed: {str(e)}"
        )
