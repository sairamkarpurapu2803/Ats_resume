"""Resume Parser Service - Extract and parse resume files"""

import fitz  # PyMuPDF
import docx
import os
import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ConfigDict
from typing import List

from utils.logger import setup_logger
from utils.errors import FileParsingError, LLMProcessingError

logger = setup_logger(__name__)

class ProfessionalExperience(BaseModel):
    """Professional experience model"""
    title: str
    company: str
    duration: str
    bullets: List[str]

class ProjectItem(BaseModel):
    """Project item model"""
    title: str
    technologies: List[str]
    description: str

class EducationItem(BaseModel):
    """Education item model"""
    degree: str
    institution: str
    year: str

class ParsedResumeSchema(BaseModel):
    """Parsed resume schema"""
    name: str = Field(description="Full name of the candidate")
    email: str = Field(description="Email address")
    phone: str = Field(description="Phone number")
    summary: str = Field(description="Existing professional summary")
    skills: List[str] = Field(description="List of all unique technical and soft skills found")
    experience: List[ProfessionalExperience] = Field(description="List of professional work experiences")
    projects: List[ProjectItem] = Field(description="List of academic or industry projects")
    education: List[EducationItem] = Field(description="List of degrees and educational institutions")
    certifications: List[str] = Field(description="List of certifications acquired")
    
    model_config = ConfigDict(populate_by_name=True)

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    try:
        text = ""
        with fitz.open(file_path) as doc:
            for page in doc:
                text += page.get_text()
        logger.info(f"Extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        raise FileParsingError(f"Failed to read PDF: {str(e)}")

def extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs if p.text])
        logger.info(f"Extracted {len(text)} characters from DOCX")
        return text
    except Exception as e:
        raise FileParsingError(f"Failed to read DOCX: {str(e)}")

def parse_resume(file_path: str) -> dict:
    """Parse resume file and extract structured data"""
    ext = os.path.splitext(file_path)[1].lower()
    
    # Extract text based on file type
    if ext == '.pdf':
        raw_text = extract_text_from_pdf(file_path)
    elif ext == '.docx':
        raw_text = extract_text_from_docx(file_path)
    else:
        raise FileParsingError("Unsupported file format. Supported: PDF, DOCX")
    
    # Get API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise LLMProcessingError("Gemini API Key missing in environment")
    
    client = genai.Client(api_key=api_key)
    
    # Retry mechanism for API calls
    max_retries = 3
    delay = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Parsing resume (attempt {attempt + 1}/{max_retries})...")
            
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=f"Extract details from this raw resume text accurately:\n\n{raw_text}",
                config=types.GenerateContentConfig(
                    system_instruction="You are an expert HR Data Extraction Assistant. Extract data exactly as written into the structure provided. Be accurate and complete.",
                    response_mime_type="application/json",
                    response_schema=ParsedResumeSchema,
                ),
            )
            
            parsed_data = json.loads(response.text)
            logger.info("Resume parsing completed successfully")
            return parsed_data
        
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Resume parsing failed after {max_retries} retries")
                raise LLMProcessingError(f"Gemini parsing failed: {str(e)}")
            
            logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff
