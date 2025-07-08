import numpy as np
from typing import List, Dict, Any
import logging
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

async def rank_resumes(
    resumes: List[Dict[str, Any]], 
    job_description: str, 
    job_embedding: List[float]
) -> List[Dict[str, Any]]:
    """
    Rank resumes based on similarity to job description
    
    Args:
        resumes: List of resume dictionaries with embeddings
        job_description: Job description text
        job_embedding: Job description embedding vector
        
    Returns:
        List of resumes ranked by similarity score
    """
    try:
        ranked_resumes = []
        
        for resume in resumes:
            if 'embedding' not in resume:
                logger.warning(f"No embedding found for resume: {resume.get('filename', 'unknown')}")
                continue
                
            # Calculate cosine similarity
            resume_embedding = np.array(resume['embedding']).reshape(1, -1)
            job_embedding_array = np.array(job_embedding).reshape(1, -1)
            
            similarity = cosine_similarity(resume_embedding, job_embedding_array)[0][0]
            
            # Add similarity score to resume
            resume['similarity_score'] = float(similarity)
            ranked_resumes.append(resume)
        
        # Sort by similarity score (descending)
        ranked_resumes.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Add rank information
        for i, resume in enumerate(ranked_resumes):
            resume['rank'] = i + 1
        
        logger.info(f"Ranked {len(ranked_resumes)} resumes")
        return ranked_resumes
        
    except Exception as e:
        logger.error(f"Error ranking resumes: {str(e)}")
        raise

async def calculate_detailed_scores(
    resumes: List[Dict[str, Any]], 
    job_description: str
) -> List[Dict[str, Any]]:
    """
    Calculate detailed scoring based on multiple factors
    
    Args:
        resumes: List of resume dictionaries
        job_description: Job description text
        
    Returns:
        List of resumes with detailed scoring
    """
    try:
        scored_resumes = []
        
        # Extract job requirements
        job_skills = extract_job_skills(job_description)
        job_experience_level = extract_experience_level(job_description)
        
        for resume in resumes:
            parsed_data = resume.get('parsed_data', {})
            
            # Calculate component scores
            skill_score = calculate_skill_match(parsed_data.get('skills', []), job_skills)
            experience_score = calculate_experience_match(
                parsed_data.get('experience', []), 
                job_experience_level
            )
            education_score = calculate_education_match(
                parsed_data.get('education', []), 
                job_description
            )
            
            # Combined score
            combined_score = (
                skill_score * 0.4 + 
                experience_score * 0.4 + 
                education_score * 0.2
            )
            
            resume['detailed_scores'] = {
                'skill_score': skill_score,
                'experience_score': experience_score,
                'education_score': education_score,
                'combined_score': combined_score
            }
            
            scored_resumes.append(resume)
        
        return scored_resumes
        
    except Exception as e:
        logger.error(f"Error calculating detailed scores: {str(e)}")
        raise

def extract_job_skills(job_description: str) -> List[str]:
    """Extract required skills from job description"""
    common_skills = [
        'python', 'javascript', 'java', 'react', 'node.js', 'sql', 'html', 'css',
        'aws', 'docker', 'kubernetes', 'git', 'linux', 'machine learning',
        'data analysis', 'project management', 'agile', 'scrum'
    ]
    
    found_skills = []
    job_lower = job_description.lower()
    
    for skill in common_skills:
        if skill in job_lower:
            found_skills.append(skill)
    
    return found_skills

def extract_experience_level(job_description: str) -> str:
    """Extract experience level from job description"""
    job_lower = job_description.lower()
    
    if 'senior' in job_lower or 'lead' in job_lower:
        return 'senior'
    elif 'junior' in job_lower or 'entry' in job_lower:
        return 'junior'
    else:
        return 'mid'

def calculate_skill_match(resume_skills: List[str], job_skills: List[str]) -> float:
    """Calculate skill match score"""
    if not job_skills:
        return 0.5  # Neutral score if no skills specified
    
    matched_skills = set(resume_skills) & set(job_skills)
    return len(matched_skills) / len(job_skills)

def calculate_experience_match(resume_experience: List[Dict], job_experience_level: str) -> float:
    """Calculate experience match score"""
    if not resume_experience:
        return 0.3  # Low score if no experience found
    
    # Simple heuristic based on number of positions
    num_positions = len(resume_experience)
    
    if job_experience_level == 'senior' and num_positions >= 3:
        return 1.0
    elif job_experience_level == 'mid' and num_positions >= 2:
        return 1.0
    elif job_experience_level == 'junior' and num_positions >= 1:
        return 1.0
    else:
        return 0.6  # Partial match

def calculate_education_match(resume_education: List[Dict], job_description: str) -> float:
    """Calculate education match score"""
    if not resume_education:
        return 0.5  # Neutral if no education found
    
    job_lower = job_description.lower()
    
    # Check for degree requirements
    if 'bachelor' in job_lower or 'degree' in job_lower:
        for edu in resume_education:
            if 'bachelor' in edu.get('degree', '').lower():
                return 1.0
        return 0.7  # Some education but not exact match
    
    return 0.8  # Good score if education present but not specifically required