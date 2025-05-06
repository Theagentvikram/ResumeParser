"""
Resume service for handling resume operations
"""
import os
import logging
import shutil
from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime

from database.models import Resume, Skill, get_db_session
from services.pdf_service import extract_text_from_pdf
from services.ollama_service import analyze_resume, generate_embedding

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Upload directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def save_resume_file(file, filename=None):
    """
    Save a resume file to the upload directory
    
    Args:
        file: File-like object
        filename: Optional filename to use
        
    Returns:
        Path to the saved file
    """
    try:
        # Generate a unique filename if not provided
        if not filename:
            ext = os.path.splitext(file.filename)[1]
            filename = f"{uuid.uuid4()}{ext}"
        
        # Create the file path
        file_path = os.path.join(UPLOAD_DIR, filename)
        
        # Save the file
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        logger.info(f"Saved resume file to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Error saving resume file: {str(e)}")
        raise Exception(f"Failed to save resume file: {str(e)}")

def process_resume(file_path):
    """
    Process a resume file and extract information
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        Dictionary with extracted information
    """
    try:
        # Extract text from the resume
        resume_text = extract_text_from_pdf(file_path)
        
        # Analyze the resume
        analysis = analyze_resume(resume_text)
        
        # Generate embedding for the resume
        embedding = generate_embedding(resume_text)
        
        # Return the results
        return {
            "text": resume_text,
            "analysis": analysis,
            "embedding": embedding
        }
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        raise Exception(f"Failed to process resume: {str(e)}")

def save_resume_to_db(file_path, analysis, resume_text, embedding):
    """
    Save resume information to the database
    
    Args:
        file_path: Path to the resume file
        analysis: Dictionary with resume analysis
        resume_text: Full text of the resume
        embedding: Vector embedding of the resume
        
    Returns:
        Resume object
    """
    try:
        # Get database session
        session = get_db_session()
        
        # Create a new resume
        resume = Resume(
            filename=os.path.basename(file_path),
            file_path=file_path,
            full_text=resume_text,
            name=analysis.get("name"),
            summary=analysis.get("summary"),
            experience_years=analysis.get("experience_years"),
            education_level=analysis.get("education_level"),
            role=analysis.get("role")
        )
        
        # Set the embedding
        import numpy as np
        resume.set_embedding(np.array(embedding))
        
        # Add skills
        for skill_name in analysis.get("skills", []):
            # Check if skill already exists
            skill = session.query(Skill).filter_by(name=skill_name).first()
            if not skill:
                # Create new skill
                skill = Skill(name=skill_name)
                session.add(skill)
            
            # Add skill to resume
            resume.skills.append(skill)
        
        # Add resume to session
        session.add(resume)
        
        # Commit changes
        session.commit()
        
        logger.info(f"Saved resume to database: {resume.id}")
        
        # Return the resume
        return resume
    except Exception as e:
        logger.error(f"Error saving resume to database: {str(e)}")
        raise Exception(f"Failed to save resume to database: {str(e)}")
    finally:
        session.close()

def get_all_resumes():
    """
    Get all resumes from the database
    
    Returns:
        List of resume dictionaries
    """
    try:
        # Get database session
        session = get_db_session()
        
        # Get all resumes
        resumes = session.query(Resume).all()
        
        # Convert to dictionaries
        result = [resume.to_dict() for resume in resumes]
        
        logger.info(f"Retrieved {len(result)} resumes")
        return result
    except Exception as e:
        logger.error(f"Error getting resumes: {str(e)}")
        raise Exception(f"Failed to get resumes: {str(e)}")
    finally:
        session.close()

def get_resume_by_id(resume_id):
    """
    Get a resume by ID
    
    Args:
        resume_id: ID of the resume
        
    Returns:
        Resume dictionary
    """
    try:
        # Get database session
        session = get_db_session()
        
        # Get the resume
        resume = session.query(Resume).filter_by(id=resume_id).first()
        
        if not resume:
            raise Exception(f"Resume not found with ID: {resume_id}")
        
        # Convert to dictionary
        result = resume.to_dict()
        
        logger.info(f"Retrieved resume: {resume.id}")
        return result
    except Exception as e:
        logger.error(f"Error getting resume: {str(e)}")
        raise Exception(f"Failed to get resume: {str(e)}")
    finally:
        session.close()

def delete_resume(resume_id):
    """
    Delete a resume by ID
    
    Args:
        resume_id: ID of the resume
        
    Returns:
        True if successful
    """
    try:
        # Get database session
        session = get_db_session()
        
        # Get the resume
        resume = session.query(Resume).filter_by(id=resume_id).first()
        
        if not resume:
            raise Exception(f"Resume not found with ID: {resume_id}")
        
        # Delete the file
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)
        
        # Delete the resume
        session.delete(resume)
        
        # Commit changes
        session.commit()
        
        logger.info(f"Deleted resume: {resume_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting resume: {str(e)}")
        raise Exception(f"Failed to delete resume: {str(e)}")
    finally:
        session.close()

def search_resumes(query, filters=None):
    """
    Search for resumes based on a query and filters
    
    Args:
        query: Search query
        filters: Dictionary of filters
        
    Returns:
        List of matching resumes
    """
    try:
        # Get database session
        session = get_db_session()
        
        # Get all resumes with embeddings
        resumes = session.query(Resume).all()
        
        # Convert to dictionaries with embeddings
        resumes_with_embeddings = []
        for resume in resumes:
            resume_dict = resume.to_dict()
            resume_dict['embedding'] = resume.get_embedding()
            resumes_with_embeddings.append(resume_dict)
        
        # Apply filters if provided
        if filters:
            filtered_resumes = []
            for resume in resumes_with_embeddings:
                include = True
                
                # Filter by graduation year
                if 'graduation_year' in filters and filters['graduation_year']:
                    # This would require adding a graduation_year field to the Resume model
                    # For now, we'll skip this filter
                    pass
                
                # Filter by skills
                if 'skills' in filters and filters['skills']:
                    resume_skills = set(resume['skills'])
                    required_skills = set(filters['skills'])
                    if not required_skills.issubset(resume_skills):
                        include = False
                
                # Filter by experience years
                if 'min_experience' in filters and filters['min_experience'] is not None:
                    if resume['experience_years'] < filters['min_experience']:
                        include = False
                
                if include:
                    filtered_resumes.append(resume)
            
            resumes_with_embeddings = filtered_resumes
        
        # If there's no query, return all resumes (after filtering)
        if not query:
            return [{'resume': r, 'score': 1.0} for r in resumes_with_embeddings]
        
        # Search using the query
        from services.ollama_service import search_resumes_by_prompt
        results = search_resumes_by_prompt(query, resumes_with_embeddings)
        
        logger.info(f"Found {len(results)} matching resumes")
        return results
    except Exception as e:
        logger.error(f"Error searching resumes: {str(e)}")
        raise Exception(f"Failed to search resumes: {str(e)}")
    finally:
        session.close()

def get_all_skills():
    """
    Get all skills from the database
    
    Returns:
        List of skill dictionaries
    """
    try:
        # Get database session
        session = get_db_session()
        
        # Get all skills
        skills = session.query(Skill).all()
        
        # Convert to dictionaries
        result = [skill.to_dict() for skill in skills]
        
        logger.info(f"Retrieved {len(result)} skills")
        return result
    except Exception as e:
        logger.error(f"Error getting skills: {str(e)}")
        raise Exception(f"Failed to get skills: {str(e)}")
    finally:
        session.close()
