"""Resume Optimizer Service - Optimize and export resumes"""

import os
import json
import time
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any
from docxtpl import DocxTemplate
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from utils.logger import setup_logger
from utils.errors import LLMProcessingError

logger = setup_logger(__name__)

class OptimizedExperience(BaseModel):
    """Optimized experience model"""
    title: str
    company: str
    duration: str
    bullets: List[str] = Field(description="Action Verb + Technology + Quantifiable Impact bullets")

class OptimizedResumeSchema(BaseModel):
    """Optimized resume schema"""
    summary: str = Field(description="80-120 word technical summary")
    skills_by_category: Dict[str, List[str]] = Field(description="Categorized technical skills")
    experience: List[OptimizedExperience] = Field(description="Enhanced experience with metrics")
    
    model_config = ConfigDict(populate_by_name=True)

def optimize_resume(
    resume_json: Dict,
    jd_text: str,
    preserve_format: bool = True
) -> Dict[str, Any]:
    """
    One-click resume optimization for ATS compatibility
    
    Rewrites resume while maintaining format and accuracy
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise LLMProcessingError("Gemini API Key not configured")
    
    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Optimize this resume for maximum ATS compatibility and job relevance.
    
    CRITICAL RULES:
    1. Never invent fake companies, metrics, or certificates
    2. Rewrite experience bullets using: Action Verb + Technology + Measurable Impact
    3. Professional summary: 80-120 words with relevant keywords
    4. Group skills by category (Cloud, DevOps, Programming, etc.)
    5. Maintain all original information accuracy
    
    Resume Data: {json.dumps(resume_json)}
    
    Job Description Target: {jd_text}
    
    Optimize and return in JSON format with:
    - summary: Tailored 80-120 word summary
    - skills_by_category: Dict with skill categories
    - experience: List with enhanced bullets
    """
    
    max_retries = 3
    delay = 2
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Optimizing resume (attempt {attempt + 1}/{max_retries})...")
            
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction="You are a premium ATS resume expert. Optimize for maximum compatibility while maintaining accuracy and truthfulness. Output valid JSON.",
                    response_mime_type="application/json",
                ),
            )
            
            optimized = json.loads(response.text)
            
            # Preserve original data for missing sections
            optimized['name'] = resume_json.get('name', 'Candidate Name')
            optimized['email'] = resume_json.get('email', 'email@example.com')
            optimized['phone'] = resume_json.get('phone', '')
            optimized['education'] = resume_json.get('education', [])
            optimized['projects'] = resume_json.get('projects', [])
            optimized['certifications'] = resume_json.get('certifications', [])
            
            logger.info("Resume optimization completed")
            return optimized
        
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Resume optimization failed after {max_retries} retries")
                raise LLMProcessingError(f"Optimization failed: {str(e)}")
            
            logger.warning(f"Attempt {attempt + 1} failed, retrying...")
            time.sleep(delay)
            delay *= 2

def generate_docx_resume(optimized_data: Dict, output_path: str):
    """
    Generate DOCX resume from optimized data
    """
    try:
        # Create document
        from docx import Document
        from docx.shared import Pt, Inches, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        doc = Document()
        
        # Set margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.5)
            section.bottom_margin = Inches(0.5)
            section.left_margin = Inches(0.5)
            section.right_margin = Inches(0.5)
        
        # Header
        name = optimized_data.get('name', 'Candidate')
        email = optimized_data.get('email', '')
        phone = optimized_data.get('phone', '')
        
        title = doc.add_paragraph()
        title_run = title.add_run(name)
        title_run.bold = True
        title_run.font.size = Pt(16)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        contact = doc.add_paragraph(f"{email} | {phone}")
        contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_runs = contact.runs
        for run in contact_runs:
            run.font.size = Pt(10)
        
        # Summary
        if optimized_data.get('summary'):
            doc.add_heading('PROFESSIONAL SUMMARY', level=2)
            doc.add_paragraph(optimized_data['summary'])
        
        # Skills
        if optimized_data.get('skills_by_category'):
            doc.add_heading('TECHNICAL SKILLS', level=2)
            for category, skills in optimized_data['skills_by_category'].items():
                if skills:
                    para = doc.add_paragraph()
                    para.add_run(f"{category}: ").bold = True
                    para.add_run(", ".join(skills))
        
        # Experience
        if optimized_data.get('experience'):
            doc.add_heading('PROFESSIONAL EXPERIENCE', level=2)
            for exp in optimized_data['experience']:
                para = doc.add_paragraph()
                para.add_run(f"{exp.get('title')} — {exp.get('company')} ({exp.get('duration')})").bold = True
                
                for bullet in exp.get('bullets', []):
                    doc.add_paragraph(f"• {bullet}", style='List Bullet')
        
        # Education
        if optimized_data.get('education'):
            doc.add_heading('EDUCATION', level=2)
            for edu in optimized_data['education']:
                if isinstance(edu, dict):
                    para = doc.add_paragraph()
                    para.add_run(f"{edu.get('degree')} — {edu.get('institution')} ({edu.get('year')})").bold = True
        
        # Certifications
        if optimized_data.get('certifications'):
            doc.add_heading('CERTIFICATIONS', level=2)
            for cert in optimized_data['certifications']:
                doc.add_paragraph(str(cert), style='List Bullet')
        
        doc.save(output_path)
        logger.info(f"DOCX resume generated: {output_path}")
    
    except Exception as e:
        logger.error(f"DOCX generation failed: {str(e)}")
        raise

def generate_pdf_resume(
    optimized_data: Dict,
    output_path: str,
    theme: str = "professional"
):
    """
    Generate PDF resume with customizable theme
    """
    try:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        
        styles = getSampleStyleSheet()
        story = []
        
        # Define custom styles
        title_style = ParagraphStyle(
            'TStyle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=RGBColor(0, 0, 0),
            spaceAfter=6,
            alignment=TA_CENTER
        )
        
        meta_style = ParagraphStyle(
            'MStyle',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=12,
            alignment=TA_CENTER
        )
        
        h1_style = ParagraphStyle(
            'H1Style',
            parent=styles['Heading2'],
            fontSize=11,
            spaceBefore=10,
            spaceAfter=4,
            textColor=RGBColor(0, 0, 0)
        )
        
        body_style = ParagraphStyle(
            'BStyle',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=3
        )
        
        bullet_style = ParagraphStyle(
            'BulletStyle',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=15,
            spaceAfter=3
        )
        
        # Header
        name = optimized_data.get('name', 'Candidate Name')
        email = optimized_data.get('email', 'email@example.com')
        phone = optimized_data.get('phone', '')
        
        story.append(Paragraph(f"<b>{name}</b>", title_style))
        story.append(Paragraph(f"{email} | {phone}", meta_style))
        story.append(Spacer(1, 8))
        
        # Professional Summary
        if optimized_data.get('summary'):
            story.append(Paragraph("<b>PROFESSIONAL SUMMARY</b>", h1_style))
            story.append(Paragraph(optimized_data['summary'], body_style))
            story.append(Spacer(1, 8))
        
        # Technical Skills
        if optimized_data.get('skills_by_category'):
            story.append(Paragraph("<b>TECHNICAL SKILLS</b>", h1_style))
            for category, skills in optimized_data['skills_by_category'].items():
                if skills:
                    skills_text = f"<b>{category}:</b> {', '.join(skills)}"
                    story.append(Paragraph(skills_text, body_style))
            story.append(Spacer(1, 8))
        
        # Professional Experience
        if optimized_data.get('experience'):
            story.append(Paragraph("<b>PROFESSIONAL EXPERIENCE</b>", h1_style))
            for exp in optimized_data['experience']:
                exp_title = f"<b>{exp.get('title')}</b> — {exp.get('company')} ({exp.get('duration')})"
                story.append(Paragraph(exp_title, body_style))
                
                for bullet in exp.get('bullets', []):
                    story.append(Paragraph(f"• {bullet}", bullet_style))
                story.append(Spacer(1, 3))
        
        # Education
        if optimized_data.get('education'):
            story.append(Paragraph("<b>EDUCATION</b>", h1_style))
            for edu in optimized_data['education']:
                if isinstance(edu, dict):
                    edu_text = f"<b>{edu.get('degree')}</b> — {edu.get('institution')} ({edu.get('year')})"
                    story.append(Paragraph(edu_text, body_style))
        
        # Certifications
        if optimized_data.get('certifications'):
            story.append(Paragraph("<b>CERTIFICATIONS</b>", h1_style))
            for cert in optimized_data['certifications']:
                story.append(Paragraph(f"• {str(cert)}", bullet_style))
        
        doc.build(story)
        logger.info(f"PDF resume generated: {output_path}")
    
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise

def generate_plaintext_resume(optimized_data: Dict, output_path: str):
    """
    Generate ATS-compatible plain text resume
    """
    try:
        lines = []
        
        # Header
        lines.append(optimized_data.get('name', 'CANDIDATE NAME'))
        lines.append('=' * 50)
        lines.append(f"Email: {optimized_data.get('email', 'email@example.com')}")
        lines.append(f"Phone: {optimized_data.get('phone', '')}")
        lines.append('')
        
        # Summary
        if optimized_data.get('summary'):
            lines.append('PROFESSIONAL SUMMARY')
            lines.append('-' * 50)
            lines.append(optimized_data['summary'])
            lines.append('')
        
        # Skills
        if optimized_data.get('skills_by_category'):
            lines.append('TECHNICAL SKILLS')
            lines.append('-' * 50)
            for category, skills in optimized_data['skills_by_category'].items():
                if skills:
                    lines.append(f"{category}: {', '.join(skills)}")
            lines.append('')
        
        # Experience
        if optimized_data.get('experience'):
            lines.append('PROFESSIONAL EXPERIENCE')
            lines.append('-' * 50)
            for exp in optimized_data['experience']:
                lines.append(f"{exp.get('title')} - {exp.get('company')}")
                lines.append(f"Duration: {exp.get('duration')}")
                for bullet in exp.get('bullets', []):
                    lines.append(f"• {bullet}")
                lines.append('')
        
        # Education
        if optimized_data.get('education'):
            lines.append('EDUCATION')
            lines.append('-' * 50)
            for edu in optimized_data['education']:
                if isinstance(edu, dict):
                    lines.append(f"{edu.get('degree')} - {edu.get('institution')} ({edu.get('year')})")
            lines.append('')
        
        # Certifications
        if optimized_data.get('certifications'):
            lines.append('CERTIFICATIONS')
            lines.append('-' * 50)
            for cert in optimized_data['certifications']:
                lines.append(f"• {str(cert)}")
        
        text = '\n'.join(lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Plain text resume generated: {output_path}")
    
    except Exception as e:
        logger.error(f"Plain text generation failed: {str(e)}")
        raise

def generate_markdown_resume(optimized_data: Dict, output_path: str):
    """
    Generate Markdown resume for GitHub/portfolio
    """
    try:
        lines = []
        
        # Header
        lines.append(f"# {optimized_data.get('name', 'Candidate Name')}")
        lines.append(f"📧 {optimized_data.get('email', 'email@example.com')} | 📱 {optimized_data.get('phone', '')}")
        lines.append('')
        
        # Summary
        if optimized_data.get('summary'):
            lines.append("## Professional Summary")
            lines.append(optimized_data['summary'])
            lines.append('')
        
        # Skills
        if optimized_data.get('skills_by_category'):
            lines.append("## Technical Skills")
            for category, skills in optimized_data['skills_by_category'].items():
                if skills:
                    lines.append(f"- **{category}**: {', '.join(skills)}")
            lines.append('')
        
        # Experience
        if optimized_data.get('experience'):
            lines.append("## Professional Experience")
            for exp in optimized_data['experience']:
                lines.append(f"### {exp.get('title')} @ {exp.get('company')}")
                lines.append(f"*{exp.get('duration')}*")
                for bullet in exp.get('bullets', []):
                    lines.append(f"- {bullet}")
                lines.append('')
        
        # Education
        if optimized_data.get('education'):
            lines.append("## Education")
            for edu in optimized_data['education']:
                if isinstance(edu, dict):
                    lines.append(f"- **{edu.get('degree')}** - {edu.get('institution')} ({edu.get('year')})")
            lines.append('')
        
        # Certifications
        if optimized_data.get('certifications'):
            lines.append("## Certifications")
            for cert in optimized_data['certifications']:
                lines.append(f"- {str(cert)}")
        
        markdown = '\n'.join(lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        logger.info(f"Markdown resume generated: {output_path}")
    
    except Exception as e:
        logger.error(f"Markdown generation failed: {str(e)}")
        raise
