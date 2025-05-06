#!/usr/bin/env python3
"""
Smart Resume Selector - FastAPI Backend
Integrates PDF extraction, Mistral summarization, and embedding-based matching
"""
import os
import uuid
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Body, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

# Import services
from services.pdf_extractor import PDFExtractor
from services.mistral_service import MistralService
from services.embedding_service import EmbeddingService
from services.database_service import DatabaseService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("smart-resume-selector")

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads", "resumes")
SUMMARIES_DIR = os.path.join(BASE_DIR, "summaries")

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SUMMARIES_DIR, exist_ok=True)

# Initialize services
pdf_extractor = PDFExtractor()
mistral_service = MistralService()
embedding_service = EmbeddingService()
db_service = DatabaseService()

# Create FastAPI app
app = FastAPI(title="Smart Resume Selector API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ResumeResponse(BaseModel):
    id: str
    name: str
    upload_date: str
    summary: str
    category: str
    experience_level: str
    key_skills: List[str]
    total_experience_years: int

class SearchQuery(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    services: Dict[str, bool]

# API Routes
@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "Smart Resume Selector API is running"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "services": {
            "pdf_extractor": True,
            "mistral": mistral_service.is_available,
            "embeddings": embedding_service.is_available,
            "database": db_service.conn is not None
        }
    }

@app.post("/resumes/upload")
async def upload_resume(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: str = Form(None)
):
    """
    Upload a resume file
    
    The file will be processed in the background to extract structured data,
    generate a summary with Mistral, and create embeddings for matching.
    """
    try:
        # Generate a unique ID for the resume
        resume_id = str(uuid.uuid4())
        
        # Create file path
        file_name = f"{resume_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        
        # Save the uploaded file
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"Saved resume file: {file_path}")
        
        # Process resume in background
        background_tasks.add_task(process_resume, resume_id, file_path)
        
        return {
            "id": resume_id,
            "filename": file.filename,
            "status": "processing",
            "message": "Resume uploaded successfully and is being processed"
        }
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading resume: {str(e)}")

@app.post("/resumes/upload-bulk")
async def upload_bulk_resumes(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...)
):
    """Upload multiple resume files"""
    try:
        results = []
        
        for file in files:
            # Generate a unique ID for the resume
            resume_id = str(uuid.uuid4())
            
            # Create file path
            file_name = f"{resume_id}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, file_name)
            
            # Save the uploaded file
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            
            logger.info(f"Saved resume file: {file_path}")
            
            # Process resume in background
            background_tasks.add_task(process_resume, resume_id, file_path)
            
            results.append({
                "id": resume_id,
                "filename": file.filename,
                "status": "processing"
            })
        
        return {
            "message": f"Uploaded {len(files)} resumes successfully",
            "resumes": results
        }
    except Exception as e:
        logger.error(f"Error uploading bulk resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading bulk resumes: {str(e)}")

@app.get("/resumes")
async def get_all_resumes():
    """Get all resumes"""
    try:
        resumes = db_service.get_all_resumes()
        
        # Format response
        response = []
        for resume in resumes:
            response.append({
                "id": resume.get("id"),
                "name": resume.get("name"),
                "upload_date": resume.get("upload_date"),
                "summary": resume.get("summary", ""),
                "category": resume.get("category", ""),
                "experience_level": resume.get("experience_level", ""),
                "key_skills": resume.get("key_skills", []),
                "total_experience_years": resume.get("total_experience_years", 0)
            })
        
        return response
    except Exception as e:
        logger.error(f"Error getting all resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting all resumes: {str(e)}")

@app.post("/resumes/search")
async def search(query: SearchQuery):
    """Search for resumes matching a query"""
    try:
        # Get all resume summaries
        resume_summaries = db_service.get_resume_summaries()
        
        # Apply filters if provided
        if query.filters:
            filtered_ids = db_service.filter_resumes(query.filters)
            if filtered_ids:
                resume_summaries = [r for r in resume_summaries if r.get("id") in filtered_ids]
        
        # Rank resumes based on query
        results = embedding_service.rank_resumes(query.query, resume_summaries, top_n=5)
        
        return results
    except Exception as e:
        logger.error(f"Error searching resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching resumes: {str(e)}")

@app.get("/resumes/{resume_id}")
async def get_resume(resume_id: str):
    """Get a specific resume by ID"""
    try:
        resume = db_service.get_resume(resume_id)
        
        if not resume:
            raise HTTPException(status_code=404, detail=f"Resume with ID {resume_id} not found")
        
        return resume
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting resume: {str(e)}")

@app.get("/resumes/{resume_id}/download")
async def download_resume(resume_id: str):
    """Download a resume file"""
    try:
        resume = db_service.get_resume(resume_id)
        
        if not resume:
            raise HTTPException(status_code=404, detail=f"Resume with ID {resume_id} not found")
        
        file_path = resume.get("file_path")
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Resume file not found")
        
        return FileResponse(file_path, filename=os.path.basename(file_path))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error downloading resume: {str(e)}")

@app.get("/skills")
async def get_all_skills():
    """Get all skills from all resumes"""
    try:
        skills = db_service.get_all_skills()
        return {"skills": skills}
    except Exception as e:
        logger.error(f"Error getting all skills: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting all skills: {str(e)}")

@app.post("/resumes/analyze")
async def analyze_resume_text(data: Dict[str, Any] = Body(...)):
    """Analyze resume text"""
    try:
        text = data.get("text")
        
        if not text:
            raise HTTPException(status_code=400, detail="No text provided")
        
        # Save text to a temporary file
        temp_file = os.path.join(UPLOAD_DIR, "temp_resume.txt")
        with open(temp_file, "w") as f:
            f.write(text)
        
        # Extract structured data
        structured_data = pdf_extractor.extract_structured_data(temp_file)
        
        # Generate summary
        summary_data = mistral_service.summarize_resume(structured_data)
        
        # Clean up
        try:
            os.remove(temp_file)
        except:
            pass
        
        return {
            "structured_data": structured_data,
            "summary": summary_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing resume text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing resume text: {str(e)}")

@app.delete("/resumes/{resume_id}")
async def delete_resume(resume_id: str):
    """Delete a resume"""
    try:
        resume = db_service.get_resume(resume_id)
        
        if not resume:
            raise HTTPException(status_code=404, detail=f"Resume with ID {resume_id} not found")
        
        # Delete from database
        success = db_service.delete_resume(resume_id)
        
        if not success:
            raise HTTPException(status_code=500, detail=f"Error deleting resume from database")
        
        # Delete file if it exists
        file_path = resume.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Error deleting resume file: {str(e)}")
        
        return {"message": f"Resume with ID {resume_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting resume: {str(e)}")

# Background task for processing resumes
async def process_resume(resume_id: str, file_path: str):
    """
    Process a resume in the background
    
    1. Extract structured data using regex
    2. Generate summary using Mistral
    3. Create embedding for matching
    4. Save to database
    """
    try:
        logger.info(f"Processing resume: {resume_id}")
        
        # Extract structured data
        structured_data = pdf_extractor.extract_structured_data(file_path)
        
        if "error" in structured_data:
            logger.error(f"Error extracting data from resume: {structured_data['error']}")
            return
        
        # Save structured data to database
        db_service.save_resume(resume_id, structured_data, file_path)
        
        # Generate summary with Mistral
        summary_data = mistral_service.summarize_resume(structured_data)
        
        # Create embedding for matching
        summary_text = summary_data.get("summary", "")
        keywords = summary_data.get("match_keywords", [])
        key_skills = summary_data.get("key_skills", [])
        
        embedding_text = summary_text
        if keywords:
            embedding_text += " " + " ".join(keywords)
        if key_skills:
            embedding_text += " " + " ".join(key_skills)
        
        embedding = embedding_service.get_embedding(embedding_text)
        
        # Save summary and embedding to database
        db_service.save_summary(resume_id, summary_data, embedding)
        
        # Save summary to file for reference
        summary_file = os.path.join(SUMMARIES_DIR, f"{resume_id}_summary.json")
        with open(summary_file, "w") as f:
            json.dump({
                "structured_data": structured_data,
                "summary": summary_data,
                "embedding_shape": str(embedding.shape) if hasattr(embedding, 'shape') else len(embedding)
            }, f, indent=2)
        
        logger.info(f"Resume processing completed for ID: {resume_id}")
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("Starting Smart Resume Selector API")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info("Shutting down Smart Resume Selector API")
    db_service.close()

# Mount static files for frontend
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "frontend", "build", "static")), name="static")

# Serve frontend index.html for all other routes
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve frontend for all other routes"""
    frontend_path = os.path.join(BASE_DIR, "frontend", "build", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    else:
        return {"message": "Frontend not built yet"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
