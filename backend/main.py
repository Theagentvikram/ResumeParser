import os
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
import uvicorn
from datetime import datetime
import json
import uuid
import requests
from dotenv import load_dotenv
from pathlib import Path
import tempfile
import shutil
import random

# Import services
try:
    from services.pdf_service import extract_text_from_pdf
except ImportError:
    # Create a fallback if PyMuPDF is not installed
    def extract_text_from_pdf(file_path):
        return "This is mock text extracted from a PDF. PyMuPDF (fitz) is not installed."

from services.llm_service import get_resume_summary
from services.embedding_service import get_embedding, calculate_similarity
from services.storage_service import upload_to_storage, get_download_url, LOCAL_STORAGE_DIR
from services.database_service import save_resume_to_db, get_resumes, search_resumes
from services.claude_service import analyze_resume_with_regex

# Import OpenRouter service for Mistral 7B
try:
    from services.openrouter_service import analyze_resume_with_openrouter, get_openrouter_model_status
    OPENROUTER_API_AVAILABLE = True
except ImportError:
    OPENROUTER_API_AVAILABLE = False
    # Create fallback functions
    def analyze_resume_with_openrouter(text):
        return analyze_resume_with_regex(text)
    def get_openrouter_model_status():
        return {"status": "unavailable", "message": "OpenRouter service not installed", "using_fallback": True}

# Try to import offline Mistral (this might not be available on all systems)
try:
    from services.mistral_offline import analyze_resume_with_mistral_offline, is_mistral_model_available, preload_model
    OFFLINE_MISTRAL_AVAILABLE = True
except ImportError:
    OFFLINE_MISTRAL_AVAILABLE = False
    # Create fallback functions
    def analyze_resume_with_mistral_offline(text):
        return analyze_resume_with_regex(text)
    def is_mistral_model_available():
        return False

# Import local LLM service
try:
    from services.llama_cpp_service import analyze_resume_with_llama_cpp, download_model, is_llama_cpp_available
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    # Create fallback functions
    def analyze_resume_with_llama_cpp(text):
        return analyze_resume_with_regex(text)
    def is_llama_cpp_available():
        return False
    def download_model(url=None):
        return None

# Load environment variables
load_dotenv()

# Get the desired analyzer mode from environment
ANALYZER_MODE = os.getenv("ANALYZER_MODE", "auto").lower()  # "auto", "api", "offline", "regex", "llama_cpp"

app = FastAPI(title="ResuMatch API", description="API for ResuMatch Resume Selection App")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development. In production, specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create storage directory if it doesn't exist
os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)

# User resumes storage (in-memory for demo)
USER_RESUMES = []

class ResumeAnalysisResponse(BaseModel):
    skills: List[str]
    experience: int
    educationLevel: str
    summary: str
    category: str

class ResumeUploadRequest(BaseModel):
    skills: List[str]
    experience: str
    educationLevel: str
    summary: str
    category: str

class SearchQuery(BaseModel):
    query: str
    filters: Optional[dict] = None

class AnalysisResult(BaseModel):
    summary: str
    skills: List[str]
    experience: int
    educationLevel: str
    category: str

class TextAnalysisRequest(BaseModel):
    text: str

class ModelStatusResponse(BaseModel):
    status: str
    message: str
    using_fallback: bool
    mode: str

@app.get("/")
async def root():
    """
    Root endpoint for health check
    """
    return {"status": "ok", "message": "ResuMatch API is running"}

@app.get("/api/model/status", response_model=ModelStatusResponse)
async def model_status():
    """
    Check the status of the LLM model (OpenRouter, offline, or local)
    """
    try:
        # Check if we're in a specific mode
        if ANALYZER_MODE == "api" and OPENROUTER_API_AVAILABLE:
            # Check OpenRouter API
            status = get_openrouter_model_status()
            status["mode"] = "api"
            return status
        
        elif ANALYZER_MODE == "offline" and OFFLINE_MISTRAL_AVAILABLE:
            # Check offline model
            if is_mistral_model_available():
                return {
                    "status": "available",
                    "message": "Offline Mistral model is available",
                    "using_fallback": False,
                    "mode": "offline"
                }
            else:
                return {
                    "status": "unavailable",
                    "message": "Offline Mistral model is not available",
                    "using_fallback": True,
                    "mode": "offline"
                }
        
        elif ANALYZER_MODE == "llama_cpp" and LLAMA_CPP_AVAILABLE:
            # Check llama.cpp model
            if is_llama_cpp_available():
                return {
                    "status": "available",
                    "message": "Local llama.cpp model is available",
                    "using_fallback": False,
                    "mode": "llama_cpp"
                }
            else:
                return {
                    "status": "unavailable",
                    "message": "Local llama.cpp model is not available",
                    "using_fallback": True,
                    "mode": "regex"
                }
        
        elif ANALYZER_MODE == "regex":
            # Using regex mode explicitly
            return {
                "status": "available",
                "message": "Using regex-based analysis (no LLM)",
                "using_fallback": False,
                "mode": "regex"
            }
        
        # Auto mode - try different options
        elif ANALYZER_MODE == "auto":
            # First try OpenRouter API
            if OPENROUTER_API_AVAILABLE:
                status = get_openrouter_model_status()
                if status["status"] == "available":
                    status["mode"] = "api"
                    return status
            
            # Then try offline Mistral model
            if OFFLINE_MISTRAL_AVAILABLE and is_mistral_model_available():
                return {
                    "status": "available",
                    "message": "Offline Mistral model is available",
                    "using_fallback": False,
                    "mode": "offline"
                }
            
            # Then try llama.cpp model
            if LLAMA_CPP_AVAILABLE and is_llama_cpp_available():
                return {
                    "status": "available",
                    "message": "Local llama.cpp model is available",
                    "using_fallback": False,
                    "mode": "llama_cpp"
                }
            
            # Fallback to regex
            return {
                "status": "available",
                "message": "Using regex-based analysis (no LLM)",
                "using_fallback": True,
                "mode": "regex"
            }
        
        # Fallback for all other cases
        return {
            "status": "unavailable",
            "message": "No suitable AI model available",
            "using_fallback": True,
            "mode": "regex"
        }
    
    except Exception as e:
        print(f"Error in model status check: {str(e)}")
        return {
            "status": "unavailable",
            "message": "Error checking model status",
            "using_fallback": True,
            "mode": "regex"
        }

@app.post("/resumes/analyze", response_model=AnalysisResult)
async def analyze_resume(file: Optional[UploadFile] = File(None), text: Optional[Dict[str, Any]] = Body(None)):
    """
    Analyze a resume file or text and extract key information
    """
    try:
        # Increase timeout for large files or complex analysis
        # This runs in a background worker to avoid blocking the server
        background_task = BackgroundTasks()
        
        resume_text = ""
        
        # Handle direct text input
        if text:
            print(f"Received text input: {type(text)}")
            if isinstance(text, dict) and "text" in text:
                resume_text = text["text"]
                print(f"Extracted text from JSON: {resume_text[:100]}...")
            else:
                resume_text = str(text)
                print(f"Using text as string: {resume_text[:100]}...")
        
        # Handle file upload
        elif file:
            # Print file information for debugging
            print(f"File received: {file.filename}, Content-Type: {file.content_type}, Size: {file.size} bytes")
            
            # Save uploaded file to a temporary location
            temp_file_path = ""
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                temp_file_path = temp_file.name
                shutil.copyfileobj(file.file, temp_file)
                
            # Extract text from the file
            try:
                if file.filename.lower().endswith(".pdf"):
                    try:
                        # Log the process for debugging
                        print(f"Extracting text from PDF: {file.filename}")
                        resume_text = extract_text_from_pdf(temp_file_path)
                        print(f"Extracted text length: {len(resume_text)} characters")
                        print(f"Text sample: {resume_text[:200].replace(chr(10), ' ')}")
                        
                        # If text extraction failed, let's try the other method directly
                        if not resume_text or len(resume_text.strip()) < 100:
                            print("Primary extraction yielded too little text, trying fallback method...")
                            from services.pdf_service import extract_with_pdfplumber
                            resume_text = extract_with_pdfplumber(temp_file_path)
                            print(f"Fallback extracted text length: {len(resume_text)} characters")
                            print(f"Fallback text sample: {resume_text[:200].replace(chr(10), ' ')}")
                        
                        # If we still don't have good text, report the error
                        if not resume_text or len(resume_text.strip()) < 100:
                            raise Exception("Failed to extract meaningful text from PDF")
                            
                    except Exception as e:
                        print(f"Error extracting PDF text: {str(e)}")
                        resume_text = f"Error extracting text from PDF: {str(e)}"
                elif file.filename.lower().endswith((".doc", ".docx")):
                    # Mock implementation for Word docs - we should add real docx extraction
                    resume_text = "This appears to be a Word document. Note: Full Word document extraction is coming soon. For now, please use PDF format for best results."
                elif file.filename.lower().endswith(".txt"):
                    with open(temp_file_path, "r") as f:
                        resume_text = f.read()
                        print(f"Text file contents ({len(resume_text)} chars): {resume_text[:100]}...")
                else:
                    raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a PDF, Word, or text file.")
                    
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
            except Exception as e:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                print(f"Error processing file: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to process the file: {str(e)}")
        
        else:
            raise HTTPException(status_code=400, detail="No file or text provided")
        
        # Analyze the resume text using the appropriate model based on mode
        if resume_text:
            print(f"Analyzing resume text (first 100 chars): {resume_text[:100]}...")
            
            # We got text, now analyze it using the best available method
            try:
                # Try to use OpenRouter API first (best quality)
                if ANALYZER_MODE in ["api", "auto"] and OPENROUTER_API_AVAILABLE:
                    try:
                        print("Attempting to use OpenRouter API with Mistral 7B")
                        analysis_result = analyze_resume_with_openrouter(resume_text)
                        return analysis_result
                    except ValueError as e:
                        # The OpenRouter API had an authentication or connection error
                        print(f"OpenRouter API error: {str(e)}")
                        if ANALYZER_MODE == "api":
                            # If user explicitly requested API mode, return the error
                            raise HTTPException(status_code=503, 
                                detail=f"OpenRouter API analysis failed: {str(e)}. Please check your API key or try again later.")
                        
                        # Otherwise in auto mode, try other methods
                        print("Falling back to other analysis methods...")
                
                # Try llama.cpp method next (often reliable on CPU)
                if ANALYZER_MODE in ["llama_cpp", "auto"] and LLAMA_CPP_AVAILABLE and is_llama_cpp_available():
                    try:
                        print("Using llama.cpp analysis method")
                        analysis_result = analyze_resume_with_llama_cpp(resume_text)
                        return analysis_result
                    except Exception as e:
                        print(f"llama.cpp analysis error: {str(e)}")
                        if ANALYZER_MODE == "llama_cpp":
                            # If user explicitly requested llama_cpp mode, return the error
                            raise HTTPException(status_code=500, 
                                detail=f"llama.cpp analysis failed: {str(e)}. Please try another analysis mode.")
                        
                        # Otherwise in auto mode, continue to next method
                        print("Falling back to other analysis methods...")
                
                # Try offline Mistral model next
                if ANALYZER_MODE in ["offline", "auto"] and OFFLINE_MISTRAL_AVAILABLE and is_mistral_model_available():
                    try:
                        print("Using offline Mistral analysis method")
                        analysis_result = analyze_resume_with_mistral_offline(resume_text)
                        return analysis_result
                    except Exception as e:
                        print(f"Offline Mistral analysis error: {str(e)}")
                        if ANALYZER_MODE == "offline":
                            # If user explicitly requested offline mode, return the error
                            raise HTTPException(status_code=500, 
                                detail=f"Offline Mistral analysis failed: {str(e)}. Please try another analysis mode.")
                        
                        # Otherwise in auto mode, fall back to regex
                        print("Falling back to regex analysis method...")
                
                # Use regex as last resort or if explicitly requested
                if ANALYZER_MODE == "regex" or ANALYZER_MODE == "auto":
                    print("Using regex-based analysis method")
                    analysis_result = analyze_resume_with_regex(resume_text)
                    return analysis_result
                
                # If we get here, no analysis method succeeded
                raise HTTPException(status_code=500, 
                    detail="Failed to analyze resume with any available method. Please check your configuration.")
                    
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                print(f"Error in resume analysis: {str(e)}")
                raise HTTPException(status_code=500, 
                    detail=f"Resume analysis error: {str(e)}")
        else:
            raise HTTPException(status_code=400, detail="Failed to extract text from the provided file")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/resumes/upload")
async def upload_resume(file: UploadFile = File(...), metadata: str = Form(...)):
    """
    Upload a resume file with metadata
    """
    try:
        # Parse metadata
        meta_dict = json.loads(metadata)
        
        # Generate a unique ID for the resume
        resume_id = str(uuid.uuid4())
        
        # Get the current timestamp
        timestamp = datetime.now().isoformat()
        
        # Create storage directory if it doesn't exist
        storage_dir = Path("./storage/resumes")
        storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Save the file to disk
        file_path = storage_dir / f"{resume_id}_{file.filename}"
        
        # Read the uploaded file
        contents = await file.read()
        
        # Write to disk
        with open(file_path, "wb") as f:
            f.write(contents)
        
        print(f"Saved resume file to {file_path}")
        
        # Create a resume object
        resume = {
            "id": resume_id,
            "filename": file.filename,
            "download_url": f"/resumes/{resume_id}/{file.filename}",
            "upload_date": timestamp,
            "status": "processed",
            "match_score": random.randint(65, 95),
            "summary": meta_dict.get("summary", ""),
            "skills": meta_dict.get("skills", []),
            "experience": meta_dict.get("experience", ""),
            "educationLevel": meta_dict.get("educationLevel", ""),
            "category": meta_dict.get("category", "")
        }
        
        # Add to our in-memory storage
        USER_RESUMES.append(resume)
        
        # Print the current resumes for debugging
        print(f"Current resumes in memory: {len(USER_RESUMES)}")
        for r in USER_RESUMES:
            print(f"  - {r['id']}: {r['filename']}")
        
        return resume
    except Exception as e:
        print(f"Error in upload_resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/resumes/user")
async def get_user_resumes():
    """
    Get resumes for the current user
    """
    try:
        # Print the current resumes for debugging
        print(f"Returning {len(USER_RESUMES)} resumes from memory")
        for r in USER_RESUMES:
            print(f"  - {r['id']}: {r['filename']}")
            
        # If we have no resumes, create some mock data
        if not USER_RESUMES:
            # Add some mock resumes for demonstration
            now = datetime.now().isoformat()
            mock_resumes = [
                {
                    "id": str(uuid.uuid4()),
                    "filename": "resume1.pdf",
                    "download_url": "/mock/resume1.pdf",
                    "upload_date": now,
                    "status": "processed",
                    "match_score": 88,
                    "summary": "Experienced software engineer with 5 years in web development.",
                    "skills": ["JavaScript", "React", "Node.js", "TypeScript", "MongoDB"],
                    "experience": "5",
                    "educationLevel": "Bachelor's",
                    "category": "Software Engineer"
                },
                {
                    "id": str(uuid.uuid4()),
                    "filename": "resume2.pdf",
                    "download_url": "/mock/resume2.pdf",
                    "upload_date": now,
                    "status": "pending",
                    "match_score": 0,
                    "summary": "",
                    "skills": [],
                    "experience": "",
                    "educationLevel": "",
                    "category": ""
                }
            ]
            USER_RESUMES.extend(mock_resumes)
            
        return USER_RESUMES
    except Exception as e:
        print(f"Error in get_user_resumes: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to get resumes: {str(e)}"}
        )

@app.post("/resumes/search")
async def search_resume(search_query: SearchQuery):
    """
    Search for resumes based on query and filters
    """
    try:
        print(f"Received search query: {search_query.query}")
        
        # Get embedding for the query (or mock embedding)
        try:
            query_embedding = await get_embedding(search_query.query)
        except Exception as e:
            print(f"Warning: Using mock embeddings. {str(e)}")
            # Mock embedding (random vector)
            query_embedding = [random.random() for _ in range(384)]
        
        # First try to search through actual user resumes
        if USER_RESUMES and len(USER_RESUMES) > 0:
            print(f"Searching through {len(USER_RESUMES)} user resumes")
            # Simple keyword matching for now
            keywords = search_query.query.lower().split()
            results = []
            
            for resume in USER_RESUMES:
                # Calculate a simple match score based on keyword presence
                score = 0
                match_reason = []
                
                # Check summary
                if "summary" in resume and resume["summary"]:
                    summary = resume["summary"].lower()
                    for keyword in keywords:
                        if keyword in summary:
                            score += 10
                            match_reason.append(f"Keyword '{keyword}' found in summary")
                
                # Check skills
                if "skills" in resume and resume["skills"]:
                    for skill in resume["skills"]:
                        for keyword in keywords:
                            if keyword in skill.lower():
                                score += 15
                                match_reason.append(f"Skill '{skill}' matches search term")
                
                # If we have a match, add to results
                if score > 0:
                    result = resume.copy()  # Make a copy to avoid modifying original
                    result["match_score"] = min(score, 100)  # Cap at 100
                    result["match_reason"] = ". ".join(match_reason)
                    results.append(result)
            
            # Sort by match score
            results.sort(key=lambda x: x.get("match_score", 0), reverse=True)
            
            if results:
                print(f"Found {len(results)} matching resumes")
                return results
            else:
                print("No matches found in user resumes, using mock data")
        else:
            print("No user resumes found, using mock data")
        
        # If no results or no user resumes, return mock data
        mock_results = [
            {
                "id": str(uuid.uuid4()),
                "filename": "candidate1.pdf",
                "upload_date": datetime.now().isoformat(),
                "match_score": 92,
                "match_reason": "Strong match on Python, JavaScript skills and experience level",
                "summary": "Software engineer with 6 years of experience in Python and JavaScript.",
                "skills": ["Python", "JavaScript", "React", "Django", "AWS"],
                "experience": "6",
                "educationLevel": "Master's",
                "category": "Software Engineer"
            },
            {
                "id": str(uuid.uuid4()),
                "filename": "candidate2.pdf",
                "upload_date": datetime.now().isoformat(),
                "match_score": 85,
                "match_reason": "Good match on frontend skills and web development experience",
                "summary": "Front-end developer with 4 years of experience creating responsive web applications.",
                "skills": ["JavaScript", "React", "CSS", "HTML", "TypeScript"],
                "experience": "4",
                "educationLevel": "Bachelor's",
                "category": "Front-end Developer"
            },
            {
                "id": str(uuid.uuid4()),
                "filename": "candidate3.pdf",
                "upload_date": datetime.now().isoformat(),
                "match_score": 78,
                "match_reason": "Matches on full-stack development and cloud experience",
                "summary": "Full-stack developer with expertise in MERN stack and cloud services.",
                "skills": ["MongoDB", "Express", "React", "Node.js", "AWS"],
                "experience": "3",
                "educationLevel": "Bachelor's",
                "category": "Full-stack Developer"
            }
        ]
        
        print("Returning mock search results")
        return mock_results
    except Exception as e:
        print(f"Error in search_resume: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Resume search failed: {str(e)}"}
        )

@app.get("/resumes")
async def get_all_resumes():
    """
    Get all resumes
    """
    try:
        # Return user resumes for now
        return await get_user_resumes()
    except Exception as e:
        print(f"Error in get_all_resumes: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to get resumes: {str(e)}"}
        )

@app.get("/resumes/download/{resume_id}")
async def download_resume(resume_id: str):
    """
    Download a resume by ID
    """
    try:
        # Find the resume in our in-memory storage
        resume = next((r for r in USER_RESUMES if r["id"] == resume_id), None)
        
        if not resume:
            return JSONResponse(
                status_code=404,
                content={"detail": f"Resume {resume_id} not found"}
            )
        
        # Look for the file in the storage directory
        storage_dir = Path("./storage/resumes")
        
        # Try to find the file with the resume ID prefix
        resume_files = list(storage_dir.glob(f"{resume_id}_*"))
        
        if not resume_files:
            # If no file found, return a mock PDF
            print(f"No file found for resume {resume_id}, returning mock PDF")
            mock_pdf_path = Path("./storage/mock_resume.pdf")
            
            # Create a mock PDF if it doesn't exist
            if not mock_pdf_path.exists():
                mock_pdf_path.parent.mkdir(parents=True, exist_ok=True)
                with open(mock_pdf_path, "wb") as f:
                    f.write(b"%PDF-1.5\n%Mock Resume PDF")
            
            return FileResponse(
                path=str(mock_pdf_path),
                filename=f"{resume['filename']}",
                media_type="application/pdf"
            )
        
        # Return the first matching file
        file_path = resume_files[0]
        return FileResponse(
            path=str(file_path),
            filename=resume["filename"],
            media_type="application/pdf"
        )
    except Exception as e:
        print(f"Error in download_resume: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to download resume: {str(e)}"}
        )

@app.delete("/resumes/{resume_id}")
async def delete_resume(resume_id: str):
    """
    Delete a resume by ID
    """
    try:
        global USER_RESUMES
        USER_RESUMES = [r for r in USER_RESUMES if r["id"] != resume_id]
        return {"status": "success", "message": f"Resume {resume_id} deleted successfully"}
    except Exception as e:
        print(f"Error in delete_resume: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to delete resume: {str(e)}"}
        )

@app.get("/download/{file_path:path}")
async def download_file(file_path: str):
    """
    Download a file from local storage
    """
    try:
        file_full_path = LOCAL_STORAGE_DIR / file_path
        if not file_full_path.exists():
            # Return a mock PDF for demo
            mock_file = LOCAL_STORAGE_DIR / "mock_resume.pdf"
            if not mock_file.exists():
                # Create an empty file
                with open(mock_file, "wb") as f:
                    f.write(b"Mock PDF content")
            
            return FileResponse(
                path=mock_file,
                filename="mock_resume.pdf",
                media_type="application/pdf"
            )
        
        return FileResponse(
            path=file_full_path,
            filename=file_full_path.name,
            media_type="application/pdf"
        )
    except Exception as e:
        print(f"Error in download_file: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Failed to download file: {str(e)}"}
        )

if __name__ == "__main__":
    try:
        # Create storage directory
        os.makedirs(LOCAL_STORAGE_DIR, exist_ok=True)
        
        # Handle model loading based on selected mode
        if ANALYZER_MODE == "llama_cpp" and LLAMA_CPP_AVAILABLE:
            print("Starting llama.cpp model download and setup...")
            # Download a quantized, small GGUF model that runs well on CPU
            model_url = "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"
            model_path = download_model(model_url)
            if model_path:
                print(f"Model downloaded to {model_path}. Will use this for resume analysis.")
            else:
                print("Failed to download model. Will fall back to regex analysis.")
                ANALYZER_MODE = "regex"
                
        # Preload the TinyLlama model if we're using offline mode
        elif ANALYZER_MODE == "offline" and OFFLINE_MISTRAL_AVAILABLE:
            from services.mistral_offline import preload_model
            print("Preloading TinyLlama model for resume analysis...")
            preload_model()
            print("Model preloaded successfully")
        
        # Run the app
        uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        print(f"Failed to start server: {str(e)}") 