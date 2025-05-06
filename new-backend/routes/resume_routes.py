"""
FastAPI routes for resume operations
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Body
from fastapi.responses import FileResponse
from typing import List, Dict, Any, Optional
import os
import logging
from pydantic import BaseModel

from services.resume_service import (
    save_resume_file,
    process_resume,
    save_resume_to_db,
    get_all_resumes,
    get_resume_by_id,
    delete_resume,
    search_resumes,
    get_all_skills
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/resumes", tags=["resumes"])

# Models
class SearchQuery(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

class ResumeResponse(BaseModel):
    id: int
    filename: str
    name: str
    summary: str
    experience_years: float
    education_level: str
    role: str
    skills: List[str]
    created_at: str

class SearchResult(BaseModel):
    resume: ResumeResponse
    score: float

@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(file: UploadFile = File(...)):
    """
    Upload a resume file and extract information
    """
    try:
        # Check file type
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Save the file
        file_path = save_resume_file(file)
        
        # Process the resume
        result = process_resume(file_path)
        
        # Save to database
        resume = save_resume_to_db(
            file_path=file_path,
            analysis=result["analysis"],
            resume_text=result["text"],
            embedding=result["embedding"]
        )
        
        # Return the resume
        return resume.to_dict()
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-bulk", response_model=List[ResumeResponse])
async def upload_bulk_resumes(files: List[UploadFile] = File(...)):
    """
    Upload multiple resume files
    """
    try:
        results = []
        
        for file in files:
            try:
                # Check file type
                if not file.filename.lower().endswith(".pdf"):
                    logger.warning(f"Skipping non-PDF file: {file.filename}")
                    continue
                
                # Save the file
                file_path = save_resume_file(file)
                
                # Process the resume
                result = process_resume(file_path)
                
                # Save to database
                resume = save_resume_to_db(
                    file_path=file_path,
                    analysis=result["analysis"],
                    resume_text=result["text"],
                    embedding=result["embedding"]
                )
                
                # Add to results
                results.append(resume.to_dict())
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                # Continue with other files
        
        return results
    except Exception as e:
        logger.error(f"Error uploading bulk resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[ResumeResponse])
async def get_resumes():
    """
    Get all resumes
    """
    try:
        return get_all_resumes()
    except Exception as e:
        logger.error(f"Error getting resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{resume_id}", response_model=ResumeResponse)
async def get_resume(resume_id: int):
    """
    Get a resume by ID
    """
    try:
        return get_resume_by_id(resume_id)
    except Exception as e:
        logger.error(f"Error getting resume: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{resume_id}")
async def remove_resume(resume_id: int):
    """
    Delete a resume by ID
    """
    try:
        delete_resume(resume_id)
        return {"message": f"Resume {resume_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting resume: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/search", response_model=List[SearchResult])
async def search(search_query: SearchQuery):
    """
    Search for resumes based on a query and filters
    """
    try:
        results = search_resumes(search_query.query, search_query.filters)
        return results
    except Exception as e:
        logger.error(f"Error searching resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{resume_id}")
async def download_resume(resume_id: int):
    """
    Download a resume file
    """
    try:
        # Get the resume
        resume = get_resume_by_id(resume_id)
        
        # Get the file path
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "resumes", resume["filename"])
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Resume file not found")
        
        return FileResponse(
            path=file_path,
            filename=resume["filename"],
            media_type="application/pdf"
        )
    except Exception as e:
        logger.error(f"Error downloading resume: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/skills/all")
async def get_skills():
    """
    Get all skills
    """
    try:
        return get_all_skills()
    except Exception as e:
        logger.error(f"Error getting skills: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
