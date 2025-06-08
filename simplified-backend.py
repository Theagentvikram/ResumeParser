#!/usr/bin/env python3
"""
Simplified ResuMatch Backend using FastAPI and llama-cpp-python
This version uses the Mistral 7B model directly with llama-cpp-python
"""

import os
import json
import logging
import tempfile
import shutil
from typing import List, Dict, Any, Optional
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn
import fitz  # PyMuPDF
from sklearn.metrics.pairwise import cosine_similarity
from llama_cpp import Llama
from fastapi import Body
import uuid
import datetime
import signal

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ResuMatch API",
    description="Simplified API for ResuMatch Resume Selection Platform",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development. In production, specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory if it doesn't exist
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads", "resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Path to the Mistral model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "backend", "models", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "backend", "models", "llama-2-7b-chat.Q4_K_M.gguf")

# Global LLM instance
llm = None

# In-memory database for resumes
resumes_db = []

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

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file"""
    try:
        logger.info(f"Extracting text from PDF: {file_path}")
        
        # Open the PDF
        try:
            doc = fitz.open(file_path)
        except Exception as e:
            logger.error(f"Error opening PDF: {str(e)}")
            # Try alternative approach with pdfplumber if available
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = ""
                    # Limit to first 5 pages for speed
                    for i in range(min(5, len(pdf.pages))):
                        text += pdf.pages[i].extract_text() or ""
                return text
            except ImportError:
                # If pdfplumber is not available, return empty string
                logger.warning("pdfplumber not available for fallback PDF extraction")
                return "Unable to extract text from PDF"
        
        # Extract text from each page (limit to first 5 pages for speed)
        text = ""
        try:
            for page_num in range(min(5, len(doc))):
                try:
                    page = doc.load_page(page_num)
                    page_text = page.get_text()
                    text += page_text
                except Exception as page_error:
                    logger.warning(f"Error extracting text from page {page_num}: {str(page_error)}")
                    continue
        except Exception as e:
            logger.error(f"Error iterating through PDF pages: {str(e)}")
        
        # Close the document
        try:
            doc.close()
        except:
            pass
        
        # If we couldn't extract any text, return a message
        if not text.strip():
            logger.warning("No text extracted from PDF")
            return "No text could be extracted from this PDF. Please try a different file."
        
        logger.info(f"Extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return "Error extracting text from PDF. Please try a different file."

def init_llm():
    """Initialize the LLM"""
    global llm
    
    if llm is not None:
        return llm
    
    try:
        logger.info(f"Loading model from {MODEL_PATH}")
        
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=4096,
            n_gpu_layers=0,  # CPU only
            verbose=False,
            n_threads=4,
            n_batch=512
        )
        
        logger.info("Model loaded successfully")
        return llm
    except Exception as e:
        logger.error(f"Error initializing LLM: {str(e)}")
        raise Exception(f"Failed to initialize LLM: {str(e)}")

def analyze_resume(resume_text):
    """Analyze a resume using the LLM"""
    try:
        # Initialize the LLM
        model = init_llm()
        
        # Truncate text if it's too long
        max_chars = 2000
        if len(resume_text) > max_chars:
            logger.info(f"Truncating resume text from {len(resume_text)} to {max_chars} characters")
            resume_text = resume_text[:max_chars]
        
        # Create a simpler prompt for faster processing
        prompt = f"""<s>[INST]Analyze this resume and extract key information as JSON:

```
{resume_text}
```

Extract only: skills (list), experience_years (number), education_level (highest degree), role (job title), name (person's name), summary (1 sentence).
Keep it very brief and simple.[/INST]

```json
"""
        
        logger.info("Generating response with LLM")
        
        # Generate completion with timeout
        try:
            # Set a timeout for the analysis
            import signal
            
            class TimeoutException(Exception):
                pass
            
            def timeout_handler(signum, frame):
                raise TimeoutException("Analysis timed out")
            
            # Set the timeout (10 seconds)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(10)
            
            # Generate completion
            response = model(
                prompt,
                max_tokens=256,
                temperature=0.1,
                top_p=0.95,
                stop=["</s>", "[/INST]"]
            )
            
            # Cancel the timeout
            signal.alarm(0)
            
            # Extract generated text
            generated_text = response["choices"][0]["text"] if "choices" in response else ""
            
        except TimeoutException:
            logger.warning("Analysis timed out, using fallback analysis")
            # Provide a fallback simple analysis
            return {
                "name": extract_name(resume_text),
                "summary": "Professional with relevant experience.",
                "skills": extract_skills(resume_text),
                "experience_years": estimate_experience(resume_text),
                "education_level": extract_education(resume_text),
                "role": extract_role(resume_text)
            }
        
        # Try to complete the JSON object if it was cut off
        if generated_text and not "}" in generated_text:
            generated_text += '}'
            
        # Make sure it starts with a proper JSON format
        if generated_text and not generated_text.startswith('{'):
            generated_text = '{' + generated_text
        
        logger.info(f"Generated response length: {len(generated_text)} chars")
        
        # Parse the JSON
        try:
            result = json.loads(generated_text)
            
            # Validate and provide defaults for missing fields
            analysis_result = {
                "name": result.get("name", extract_name(resume_text)),
                "summary": result.get("summary", "Professional with relevant skills and experience."),
                "skills": result.get("skills", extract_skills(resume_text)),
                "experience_years": float(result.get("experience_years", estimate_experience(resume_text))),
                "education_level": result.get("education_level", extract_education(resume_text)),
                "role": result.get("role", extract_role(resume_text))
            }
            
            # Ensure skills is a list
            if not isinstance(analysis_result["skills"], list):
                if isinstance(analysis_result["skills"], str):
                    # Split by commas if it's a string
                    analysis_result["skills"] = [skill.strip() for skill in analysis_result["skills"].split(",")]
                else:
                    analysis_result["skills"] = []
            
            logger.info(f"Successfully extracted {len(analysis_result['skills'])} skills")
            return analysis_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing response as JSON: {str(e)}")
            logger.debug(f"Raw response: {generated_text[:200]}...")
            
            # Use fallback analysis
            return {
                "name": extract_name(resume_text),
                "summary": "Professional with relevant experience.",
                "skills": extract_skills(resume_text),
                "experience_years": estimate_experience(resume_text),
                "education_level": extract_education(resume_text),
                "role": extract_role(resume_text)
            }
            
    except Exception as e:
        logger.error(f"Error in resume analysis: {str(e)}")
        # Use fallback analysis
        return {
            "name": extract_name(resume_text),
            "summary": "Professional with relevant experience.",
            "skills": extract_skills(resume_text),
            "experience_years": estimate_experience(resume_text),
            "education_level": extract_education(resume_text),
            "role": extract_role(resume_text)
        }

# Fallback extraction functions
def extract_name(text):
    """Extract name from resume text using simple heuristics"""
    lines = text.split('\n')
    # Assume the name is in the first few lines
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) < 40 and not any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum', 'vitae', 'address', 'phone', 'email']):
            return line
    return "Unknown"

def extract_skills(text):
    """Extract skills from resume text using simple heuristics"""
    text = text.lower()
    common_skills = [
        "python", "javascript", "java", "c++", "c#", "ruby", "php", "swift", "kotlin", "go",
        "react", "angular", "vue", "node.js", "express", "django", "flask", "spring", "asp.net",
        "html", "css", "sql", "nosql", "mongodb", "mysql", "postgresql", "oracle", "firebase",
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git", "github", "gitlab",
        "agile", "scrum", "kanban", "jira", "confluence", "leadership", "management", "communication",
        "teamwork", "problem-solving", "critical thinking", "creativity", "time management"
    ]
    
    found_skills = []
    for skill in common_skills:
        if skill in text:
            found_skills.append(skill.title())  # Capitalize skill names
    
    # If no skills found, return some generic ones
    if not found_skills:
        return ["Communication", "Problem Solving", "Teamwork"]
    
    return found_skills[:10]  # Limit to 10 skills

def estimate_experience(text):
    """Estimate years of experience from resume text"""
    text = text.lower()
    # Look for patterns like "X years of experience" or "X+ years"
    import re
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of)?\s*experience',
        r'experience\s*(?:of)?\s*(\d+)\+?\s*years?',
        r'worked\s*(?:for)?\s*(\d+)\+?\s*years?'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                pass
    
    # If no explicit mention, try to estimate from work history
    # Count the number of job positions
    job_indicators = ["experience", "work experience", "employment", "career"]
    job_count = 0
    
    for indicator in job_indicators:
        if indicator in text:
            job_count += 1
    
    # Assume average of 2 years per position
    if job_count > 0:
        return min(job_count * 2, 15)  # Cap at 15 years
    
    return 1  # Default to 1 year

def extract_education(text):
    """Extract highest education level from resume text"""
    text = text.lower()
    
    # Check for degrees in order of highest to lowest
    if any(term in text for term in ["phd", "ph.d", "doctorate", "doctoral"]):
        return "PhD"
    elif any(term in text for term in ["master", "ms ", "m.s", "msc", "m.sc", "ma ", "m.a", "mba", "m.b.a"]):
        return "Master's"
    elif any(term in text for term in ["bachelor", "bs ", "b.s", "ba ", "b.a", "bsc", "b.sc"]):
        return "Bachelor's"
    elif any(term in text for term in ["associate", "a.s", "a.a"]):
        return "Associate's"
    elif any(term in text for term in ["high school", "secondary", "hs ", "h.s"]):
        return "High School"
    
    return "Bachelor's"  # Default to Bachelor's

def extract_role(text):
    """Extract job role from resume text"""
    text = text.lower()
    
    # Common job titles
    job_titles = [
        "software engineer", "software developer", "web developer", "frontend developer", 
        "backend developer", "full stack developer", "data scientist", "data analyst",
        "product manager", "project manager", "program manager", "business analyst",
        "ux designer", "ui designer", "graphic designer", "marketing manager",
        "sales manager", "account manager", "customer success manager", "operations manager",
        "human resources", "hr manager", "recruiter", "talent acquisition"
    ]
    
    for title in job_titles:
        if title in text:
            return title.title()  # Capitalize title
    
    # If no specific title found, try to extract from the first few lines
    lines = text.split('\n')
    for line in lines[:10]:
        line = line.strip().lower()
        if any(keyword in line for keyword in ["engineer", "developer", "manager", "analyst", "designer", "specialist", "consultant"]):
            return line.title()
    
    return "Professional"  # Default role

def generate_embedding(text):
    """Generate an embedding for a text using the LLM"""
    try:
        # Initialize the LLM
        model = init_llm()
        
        # Truncate text if it's too long
        max_chars = 2000
        if len(text) > max_chars:
            logger.info(f"Truncating text from {len(text)} to {max_chars} characters")
            text = text[:max_chars]
        
        # Create a prompt for embedding
        prompt = f"Represent this text for semantic search: {text}"
        
        # Generate embedding
        response = model(
            prompt,
            max_tokens=1,  # We only need the embedding, not the output
            temperature=0.0,
            embedding=True
        )
        
        # Return the embedding
        return response.get("embedding", [])
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise Exception(f"Failed to generate embedding: {str(e)}")

@app.post("/api/resumes/upload")
async def upload_resume(file: UploadFile = File(...), metadata: str = Form(None)):
    """
    Upload a resume file and extract information
    """
    try:
        logger.info(f"Received resume upload: {file.filename}")
        
        # Check if file is a PDF
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"Invalid file type: {file.filename}")
            return {"message": "Only PDF files are supported"}
        
        # Create a unique ID for the resume
        resume_id = str(uuid.uuid4())
        
        # Create directory if it doesn't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(UPLOAD_DIR, f"{resume_id}.pdf")
        try:
            contents = await file.read()
            with open(file_path, "wb") as f:
                f.write(contents)
            logger.info(f"Saved resume to {file_path}")
        except Exception as e:
            logger.error(f"Error saving file: {str(e)}")
            return {"message": f"Error saving file: {str(e)}"}
        
        # Extract text from PDF
        resume_text = extract_text_from_pdf(file_path)
        
        # If we couldn't extract any text, return an error
        if resume_text.startswith("Error") or resume_text.startswith("No text") or resume_text.startswith("Unable"):
            return {"message": resume_text}
        
        # Parse metadata if provided
        meta = {}
        if metadata:
            try:
                meta = json.loads(metadata)
            except:
                logger.warning(f"Invalid metadata: {metadata}")
        
        # Process the resume with a timeout
        try:
            # Set a timeout for the analysis
            import signal
            
            class TimeoutException(Exception):
                pass
            
            def timeout_handler(signum, frame):
                raise TimeoutException("Analysis timed out")
            
            # Set the timeout (10 seconds)
            original_handler = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(10)
            
            try:
                # Analyze the resume
                analysis = analyze_resume(resume_text)
                
                # Cancel the timeout
                signal.alarm(0)
                
            except TimeoutException:
                logger.warning("Resume analysis timed out, using fallback analysis")
                # Use fallback analysis
                analysis = {
                    "name": extract_name(resume_text),
                    "summary": "Professional with relevant experience.",
                    "skills": extract_skills(resume_text),
                    "experience_years": estimate_experience(resume_text),
                    "education_level": extract_education(resume_text),
                    "role": extract_role(resume_text)
                }
            finally:
                # Reset the alarm
                signal.alarm(0)
                signal.signal(signal.SIGALRM, original_handler)
        
        except Exception as e:
            logger.error(f"Error analyzing resume: {str(e)}")
            # Use fallback analysis
            analysis = {
                "name": extract_name(resume_text),
                "summary": "Professional with relevant experience.",
                "skills": extract_skills(resume_text),
                "experience_years": estimate_experience(resume_text),
                "education_level": extract_education(resume_text),
                "role": extract_role(resume_text)
            }
        
        # Generate embedding
        try:
            embedding = generate_embedding(resume_text)
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            embedding = []
        
        # Create a resume object
        resume = {
            "id": resume_id,
            "filename": file.filename,
            "file_path": file_path,
            "upload_date": datetime.now().isoformat(),
            "text": resume_text,
            "analysis": analysis,
            "embedding": embedding,
            "metadata": meta
        }
        
        # Add to the in-memory database
        resumes_db.append(resume)
        
        logger.info(f"Resume processed successfully: {resume_id}")
        
        # Return the resume data
        return {
            "id": resume_id,
            "filename": file.filename,
            "upload_date": resume["upload_date"],
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error processing resume: {str(e)}")
        return {"message": f"Error processing resume: {str(e)}"}

@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "status": "ok",
        "message": "ResuMatch Simplified API is running",
        "docs_url": "/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.0.0"
    }

@app.post("/api/resumes/upload-bulk")
async def upload_bulk_resumes(files: List[UploadFile] = File(...)):
    """Upload multiple resume files"""
    try:
        results = []
        
        for file in files:
            try:
                # Check file type
                if not file.filename.lower().endswith(".pdf"):
                    logger.warning(f"Skipping non-PDF file: {file.filename}")
                    continue
                
                # Save the file
                filename = f"{len(resumes_db) + 1}_{file.filename}"
                file_path = os.path.join(UPLOAD_DIR, filename)
                
                with open(file_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                
                # Extract text from the resume
                resume_text = extract_text_from_pdf(file_path)
                
                # Analyze the resume
                analysis = analyze_resume(resume_text)
                
                # Generate embedding for the resume
                embedding = generate_embedding(resume_text)
                
                # Create a resume object
                resume = {
                    "id": len(resumes_db) + 1,
                    "filename": filename,
                    "file_path": file_path,
                    "full_text": resume_text,
                    "name": analysis.get("name"),
                    "summary": analysis.get("summary"),
                    "experience_years": analysis.get("experience_years"),
                    "education_level": analysis.get("education_level"),
                    "role": analysis.get("role"),
                    "skills": analysis.get("skills"),
                    "embedding": embedding,
                    "created_at": "2025-05-05"  # Simplified date
                }
                
                # Add to database
                resumes_db.append(resume)
                
                # Add to results
                results.append({
                    "id": resume["id"],
                    "filename": resume["filename"],
                    "name": resume["name"],
                    "summary": resume["summary"],
                    "experience_years": resume["experience_years"],
                    "education_level": resume["education_level"],
                    "role": resume["role"],
                    "skills": resume["skills"],
                    "created_at": resume["created_at"]
                })
                
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                # Continue with other files
        
        return results
    except Exception as e:
        logger.error(f"Error uploading bulk resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resumes")
async def get_resumes():
    """Get all resumes"""
    try:
        results = []
        
        for resume in resumes_db:
            results.append({
                "id": resume["id"],
                "filename": resume["filename"],
                "name": resume["name"],
                "summary": resume["summary"],
                "experience_years": resume["experience_years"],
                "education_level": resume["education_level"],
                "role": resume["role"],
                "skills": resume["skills"],
                "created_at": resume["created_at"]
            })
        
        return results
    except Exception as e:
        logger.error(f"Error getting resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resumes/{resume_id}")
async def get_resume(resume_id: int):
    """Get a resume by ID"""
    try:
        for resume in resumes_db:
            if resume["id"] == resume_id:
                return {
                    "id": resume["id"],
                    "filename": resume["filename"],
                    "name": resume["name"],
                    "summary": resume["summary"],
                    "experience_years": resume["experience_years"],
                    "education_level": resume["education_level"],
                    "role": resume["role"],
                    "skills": resume["skills"],
                    "created_at": resume["created_at"]
                }
        
        raise HTTPException(status_code=404, detail=f"Resume not found with ID: {resume_id}")
    except Exception as e:
        logger.error(f"Error getting resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/resumes/{resume_id}")
async def delete_resume(resume_id: int):
    """Delete a resume by ID"""
    try:
        for i, resume in enumerate(resumes_db):
            if resume["id"] == resume_id:
                # Delete the file
                if os.path.exists(resume["file_path"]):
                    os.remove(resume["file_path"])
                
                # Remove from database
                resumes_db.pop(i)
                
                return {"message": f"Resume {resume_id} deleted successfully"}
        
        raise HTTPException(status_code=404, detail=f"Resume not found with ID: {resume_id}")
    except Exception as e:
        logger.error(f"Error deleting resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/resumes/search")
async def search_resumes(search_query: SearchQuery):
    """Search for resumes based on a query and filters"""
    try:
        # Generate embedding for the query
        query_embedding = generate_embedding(search_query.query)
        
        # Apply filters if provided
        filtered_resumes = []
        for resume in resumes_db:
            include = True
            
            # Filter by skills
            if search_query.filters and "skills" in search_query.filters and search_query.filters["skills"]:
                resume_skills = set(resume["skills"])
                required_skills = set(search_query.filters["skills"])
                if not required_skills.issubset(resume_skills):
                    include = False
            
            # Filter by experience years
            if search_query.filters and "min_experience" in search_query.filters and search_query.filters["min_experience"] is not None:
                if resume["experience_years"] < search_query.filters["min_experience"]:
                    include = False
            
            if include:
                filtered_resumes.append(resume)
        
        # Calculate similarity scores
        results = []
        query_embedding_array = np.array(query_embedding).reshape(1, -1)
        
        for resume in filtered_resumes:
            if "embedding" in resume and resume["embedding"]:
                resume_embedding = np.array(resume["embedding"]).reshape(1, -1)
                similarity = float(cosine_similarity(query_embedding_array, resume_embedding)[0][0])
                
                # Add to results
                results.append({
                    "resume": {
                        "id": resume["id"],
                        "filename": resume["filename"],
                        "name": resume["name"],
                        "summary": resume["summary"],
                        "experience_years": resume["experience_years"],
                        "education_level": resume["education_level"],
                        "role": resume["role"],
                        "skills": resume["skills"],
                        "created_at": resume["created_at"]
                    },
                    "score": similarity
                })
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top 5 results
        return results[:5]
    except Exception as e:
        logger.error(f"Error searching resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/resumes/download/{resume_id}")
async def download_resume(resume_id: int):
    """Download a resume file"""
    try:
        for resume in resumes_db:
            if resume["id"] == resume_id:
                if not os.path.exists(resume["file_path"]):
                    raise HTTPException(status_code=404, detail="Resume file not found")
                
                return FileResponse(
                    path=resume["file_path"],
                    filename=resume["filename"],
                    media_type="application/pdf"
                )
        
        raise HTTPException(status_code=404, detail=f"Resume not found with ID: {resume_id}")
    except Exception as e:
        logger.error(f"Error downloading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/skills")
async def get_skills():
    """Get all skills from resumes"""
    try:
        all_skills = set()
        
        for resume in resumes_db:
            all_skills.update(resume["skills"])
        
        return list(all_skills)
    except Exception as e:
        logger.error(f"Error getting skills: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/resumes/analyze")
async def analyze_resume_endpoint(file: Optional[UploadFile] = File(None), text: Optional[Dict[str, Any]] = Body(None)):
    """
    Analyze a resume file or text and extract key information
    """
    try:
        resume_text = ""
        
        # Handle direct text input
        if text:
            if isinstance(text, dict) and "text" in text:
                resume_text = text["text"]
            else:
                resume_text = str(text)
        
        # Handle file upload
        elif file:
            # Save uploaded file to a temporary location
            temp_file_path = ""
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
                temp_file_path = temp_file.name
                shutil.copyfileobj(file.file, temp_file)
                
            # Extract text from the file
            try:
                if file.filename.lower().endswith(".pdf"):
                    resume_text = extract_text_from_pdf(temp_file_path)
                elif file.filename.lower().endswith((".doc", ".docx")):
                    resume_text = "This appears to be a Word document. Note: Full Word document extraction is coming soon."
                elif file.filename.lower().endswith(".txt"):
                    with open(temp_file_path, "r") as f:
                        resume_text = f.read()
                else:
                    raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a PDF, Word, or text file.")
                    
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
            except Exception as e:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                raise HTTPException(status_code=500, detail=f"Failed to process the file: {str(e)}")
        
        else:
            raise HTTPException(status_code=400, detail="No file or text provided")
        
        # Analyze the resume text
        if resume_text:
            analysis_result = analyze_resume(resume_text)
            return analysis_result
        else:
            raise HTTPException(status_code=400, detail="Failed to extract text from the provided file")
            
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize the LLM on startup"""
    try:
        # Initialize the LLM
        init_llm()
        logger.info("LLM initialized successfully")
        
        # Create upload directory
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        logger.info(f"Upload directory created at {UPLOAD_DIR}")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("simplified-backend:app", host="0.0.0.0", port=8001, reload=True)
