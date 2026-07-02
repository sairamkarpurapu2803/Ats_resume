"""ATS Analysis Service - Analyze resume compatibility with job descriptions"""

import os
import json
import time
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, List, Any

from utils.logger import setup_logger
from utils.errors import LLMProcessingError

logger = setup_logger(__name__)

# Initialize semantic model (cached globally)
_semantic_model = None

def get_semantic_model():
    """Get or initialize semantic model"""
    global _semantic_model
    if _semantic_model is None:
        logger.info("Loading semantic model...")
        _semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _semantic_model

def extract_jd_keywords(jd_text: str) -> Dict[str, Any]:
    """
    Extract structured keywords from job description using Gemini
    
    Returns:
    {
        'technical_skills': [...],
        'nice_to_have': [...],
        'soft_skills': [...],
        'seniority_level': str,
        'years_experience': int
    }
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise LLMProcessingError("Gemini API Key not configured")
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Extract and categorize skills from this job description.
    Return JSON with:
    - technical_skills: Required technical skills
    - nice_to_have: Optional but beneficial skills
    - soft_skills: Communication, leadership, teamwork, etc.
    - seniority_level: junior, mid, senior, lead
    - years_experience: Minimum years required
    
    Job Description:
    {jd_text}
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            
            result = json.loads(response.text)
            logger.info(f"Extracted {len(result.get('technical_skills', []))} technical skills from JD")
            return result
        
        except Exception as e:
            if attempt == max_retries - 1:
                raise LLMProcessingError(f"JD keyword extraction failed: {str(e)}")
            time.sleep(2 ** attempt)

def analyze_ats_matching(resume_data: Dict, jd_keywords: Dict) -> Dict[str, Any]:
    """
    Analyze resume against JD keywords using semantic matching
    
    Returns matching analysis with scores
    """
    model = get_semantic_model()
    
    resume_skills = [s.lower().strip() for s in resume_data.get("skills", [])]
    jd_technical = [s.lower().strip() for s in jd_keywords.get("technical_skills", [])]
    jd_nice_to_have = [s.lower().strip() for s in jd_keywords.get("nice_to_have", [])]
    
    if not resume_skills:
        logger.warning("No skills found in resume")
        return {
            "matched_skills": [],
            "missing_skills": jd_technical,
            "match_percentage": 0,
            "suggestions": ["Add more skills to your resume"]
        }
    
    # Encode for semantic similarity
    resume_embeddings = model.encode(resume_skills, convert_to_tensor=True)
    jd_embeddings = model.encode(jd_technical, convert_to_tensor=True)
    
    # Calculate similarity scores
    matched_skills = []
    missing_skills = []
    
    for jd_skill in jd_technical:
        jd_emb = model.encode(jd_skill, convert_to_tensor=True)
        similarities = model.util.pytorch_cos_sim(jd_emb, resume_embeddings)[0]
        max_similarity = float(similarities.max())
        
        if max_similarity > 0.7:  # 70% similarity threshold
            matched_skills.append(jd_skill)
        else:
            missing_skills.append(jd_skill)
    
    match_percentage = int((len(matched_skills) / len(jd_technical)) * 100) if jd_technical else 0
    
    suggestions = []
    if match_percentage < 50:
        suggestions.append(f"Add more relevant skills. Current match: {match_percentage}%")
    
    missing_top_3 = missing_skills[:3]
    if missing_top_3:
        suggestions.append(f"Priority skills to add: {', '.join(missing_top_3)}")
    
    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "match_percentage": match_percentage,
        "suggestions": suggestions
    }

def validate_sections(resume_data: Dict) -> Dict[str, Any]:
    """
    Validate all resume sections
    
    Returns validation scores and missing sections
    """
    section_scores = {}
    
    # Validate each section
    section_scores['contact_info'] = 100 if (resume_data.get('name') and resume_data.get('email')) else 0
    section_scores['summary'] = 100 if resume_data.get('summary') and len(resume_data.get('summary', '')) > 50 else 50 if resume_data.get('summary') else 0
    section_scores['skills'] = min(100, len(resume_data.get('skills', [])) * 10)  # 10% per skill up to 100%
    section_scores['experience'] = min(100, len(resume_data.get('experience', [])) * 25)  # 25% per position
    section_scores['education'] = 100 if resume_data.get('education') else 70
    section_scores['projects'] = min(100, len(resume_data.get('projects', [])) * 50)  # 50% per project
    
    completeness = sum(section_scores.values()) / len(section_scores)
    
    missing_sections = [k for k, v in section_scores.items() if v == 0]
    
    return {
        "section_scores": section_scores,
        "completeness": completeness,
        "missing_sections": missing_sections
    }

def detect_missing_skills(resume_data: Dict, jd_text: str) -> Dict[str, Any]:
    """
    Detailed skill gap analysis
    
    Categorizes missing skills by priority
    """
    jd_keywords = extract_jd_keywords(jd_text)
    resume_skills = [s.lower() for s in resume_data.get('skills', [])]
    
    technical_skills = jd_keywords.get('technical_skills', [])
    nice_to_have = jd_keywords.get('nice_to_have', [])
    soft_skills = jd_keywords.get('soft_skills', [])
    
    critical_missing = [s for s in technical_skills if s.lower() not in resume_skills]
    recommended_missing = [s for s in nice_to_have if s.lower() not in resume_skills]
    
    total_skills = len(technical_skills) + len(nice_to_have)
    covered_skills = len(technical_skills) - len(critical_missing)
    gap_percentage = ((len(critical_missing) + len(recommended_missing)) / total_skills * 100) if total_skills > 0 else 0
    
    return {
        "critical_missing": critical_missing[:5],
        "recommended": recommended_missing[:5],
        "soft_skills": soft_skills,
        "gap_percentage": gap_percentage,
        "categories": {
            "technical": {"missing": len(critical_missing), "required": len(technical_skills)},
            "nice_to_have": {"missing": len(recommended_missing), "total": len(nice_to_have)},
            "soft_skills": {"count": len(soft_skills)}
        }
    }

def calculate_ats_score(matching_analysis: Dict, section_validation: Dict) -> int:
    """
    Calculate comprehensive ATS score (0-100)
    
    Weighted scoring:
    - Keyword matching: 40%
    - Section validation: 30%
    - Skills completeness: 20%
    - Format & structure: 10%
    """
    match_score = matching_analysis.get('match_percentage', 0) * 0.40
    section_score = min(100, section_validation.get('completeness', 0)) * 0.30
    skills_score = min(100, len(section_validation.get('section_scores', {}).get('skills', 0))) * 0.20
    format_score = 10  # Default format score
    
    total_score = match_score + section_score + skills_score + format_score
    
    # Cap at 100, minimum 20 (for basic structure)
    final_score = max(20, min(100, int(total_score)))
    
    logger.info(f"Calculated ATS score: {final_score}")
    return final_score
