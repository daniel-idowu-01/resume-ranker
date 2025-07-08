import re
import json
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

async def parse_resume(text_content: str) -> Dict[str, Any]:
    """
    Parse resume text to extract structured information
    
    Args:
        text_content: Raw text from resume
        
    Returns:
        Dictionary containing parsed resume data
    """
    try:
        parsed_data = {
            "name": extract_name(text_content),
            "email": extract_email(text_content),
            "phone": extract_phone(text_content),
            "skills": extract_skills(text_content),
            "education": extract_education(text_content),
            "experience": extract_experience(text_content),
            "certifications": extract_certifications(text_content),
            "summary": extract_summary(text_content)
        }
        
        return parsed_data
        
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
        return {"error": str(e)}

def extract_name(text: str) -> Optional[str]:
    """Extract name from resume text"""
    # Simple regex patterns for name extraction
    lines = text.split('\n')[:5]  # Check first 5 lines
    
    for line in lines:
        line = line.strip()
        if len(line) > 0 and len(line) < 50:
            # Basic name pattern
            if re.match(r'^[A-Za-z\s\.]+$', line) and len(line.split()) >= 2:
                return line
    
    return None

def extract_email(text: str) -> Optional[str]:
    """Extract email from resume text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(email_pattern, text)
    return matches[0] if matches else None

def extract_phone(text: str) -> Optional[str]:
    """Extract phone number from resume text"""
    phone_pattern = r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    matches = re.findall(phone_pattern, text)
    return matches[0] if matches else None

def extract_skills(text: str) -> List[str]:
    """Extract skills from resume text"""
    skills = []
    
    # Common skill keywords
    skill_keywords = [
        'python', 'javascript', 'java', 'react', 'node.js', 'sql', 'html', 'css',
        'aws', 'docker', 'kubernetes', 'git', 'linux', 'machine learning',
        'data analysis', 'project management', 'agile', 'scrum'
    ]
    
    text_lower = text.lower()
    for skill in skill_keywords:
        if skill in text_lower:
            skills.append(skill)
    
    return skills

def extract_education(text: str) -> List[Dict[str, str]]:
    """Extract education information"""
    education = []
    
    # Look for degree patterns
    degree_patterns = [
        r'(bachelor|master|phd|doctorate|b\.s\.|m\.s\.|b\.a\.|m\.a\.)[\s\w]*',
        r'(university|college|institute)[\s\w]*',
    ]
    
    for pattern in degree_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            education.append({
                "degree": match,
                "institution": "Not specified",
                "year": "Not specified"
            })
    
    return education

def extract_experience(text: str) -> List[Dict[str, str]]:
    """Extract work experience"""
    experience = []
    
    # Look for job title patterns
    job_patterns = [
        r'(software engineer|developer|manager|analyst|consultant|director)',
        r'(senior|junior|lead|principal)[\s\w]*',
    ]
    
    for pattern in job_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            experience.append({
                "title": match,
                "company": "Not specified",
                "duration": "Not specified"
            })
    
    return experience

def extract_certifications(text: str) -> List[str]:
    """Extract certifications"""
    cert_keywords = [
        'aws certified', 'microsoft certified', 'cisco certified',
        'pmp', 'scrum master', 'agile certified'
    ]
    
    certifications = []
    text_lower = text.lower()
    
    for cert in cert_keywords:
        if cert in text_lower:
            certifications.append(cert)
    
    return certifications

def extract_summary(text: str) -> Optional[str]:
    """Extract professional summary"""
    lines = text.split('\n')
    
    # Look for summary sections
    summary_keywords = ['summary', 'objective', 'profile', 'about']
    
    for i, line in enumerate(lines):
        if any(keyword in line.lower() for keyword in summary_keywords):
            # Take next few lines as summary
            summary_lines = lines[i+1:i+5]
            summary = ' '.join(summary_lines).strip()
            if len(summary) > 20:
                return summary
    
    return None