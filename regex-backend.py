#!/usr/bin/env python3
"""
Simplified backend for ResuMatch using regex-based extraction
"""
import os
import re
import json
import uuid
import logging
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

import fitz  # PyMuPDF
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simplified-backend")

# Constants
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads", "resumes")
os.makedirs(UPLOAD_DIR, exist_ok=True)
logger.info(f"Upload directory created at {UPLOAD_DIR}")

# In-memory database for resumes
resumes = []

# Create FastAPI app
app = FastAPI(title="ResuMatch Simplified API")

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
    filename: str
    upload_date: str
    analysis: Dict[str, Any]

class SearchQuery(BaseModel):
    query: str
    filters: Optional[Dict[str, Any]] = None

# Helper functions
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

def extract_name(text):
    """Extract name from resume text using regex"""
    lines = text.split('\n')
    # Assume the name is in the first few lines
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) < 40 and not any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum', 'vitae', 'address', 'phone', 'email']):
            return line
    return "Unknown"

def extract_email(text):
    """Extract email from resume text using regex"""
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else "Unknown"

def extract_phone(text):
    """Extract phone number from resume text using regex"""
    phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, text)
    return phones[0] if phones else "Unknown"

def extract_skills(text):
    """Extract skills from resume text using regex"""
    text = text.lower()
    
    # Common technical skills
    tech_skills = [
        "python", "javascript", "typescript", "java", "c++", "c#", "ruby", "php", "swift", "kotlin", "go",
        "react", "angular", "vue", "node.js", "express", "django", "flask", "spring", "asp.net",
        "html", "css", "sass", "less", "bootstrap", "tailwind", "material-ui", "jquery",
        "sql", "nosql", "mongodb", "mysql", "postgresql", "oracle", "firebase", "redis", "elasticsearch",
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git", "github", "gitlab", "bitbucket",
        "rest", "graphql", "grpc", "microservices", "serverless", "ci/cd", "devops", "mlops",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn",
        "machine learning", "deep learning", "natural language processing", "computer vision", "data science",
        "agile", "scrum", "kanban", "jira", "confluence", "trello", "asana"
    ]
    
    # Common soft skills
    soft_skills = [
        "leadership", "management", "communication", "teamwork", "problem-solving", "critical thinking",
        "creativity", "time management", "organization", "adaptability", "flexibility", "resilience",
        "emotional intelligence", "conflict resolution", "negotiation", "presentation", "public speaking",
        "customer service", "client relations", "mentoring", "coaching", "collaboration", "attention to detail"
    ]
    
    # Combine all skills
    all_skills = tech_skills + soft_skills
    
    # Find skills in text
    found_skills = []
    for skill in all_skills:
        if skill in text:
            # Make sure it's a whole word match
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text):
                found_skills.append(skill.title())  # Capitalize skill names
    
    # If no skills found, return some generic ones
    if not found_skills:
        return ["Communication", "Problem Solving", "Teamwork"]
    
    return sorted(list(set(found_skills)))[:15]  # Limit to 15 unique skills

def extract_education(text):
    """Extract education from resume text using regex"""
    text = text.lower()
    
    # Define education patterns
    education_patterns = {
        "PhD": [r'ph\.?d\.?', r'doctor of philosophy', r'doctorate'],
        "Master's": [r'master', r'm\.s\.', r'm\.a\.', r'mba', r'msc'],
        "Bachelor's": [r'bachelor', r'b\.s\.', r'b\.a\.', r'bsc', r'undergraduate'],
        "Associate's": [r'associate', r'a\.s\.', r'a\.a\.'],
        "High School": [r'high school', r'secondary', r'hs diploma']
    }
    
    # Check for each education level
    for level, patterns in education_patterns.items():
        for pattern in patterns:
            if re.search(r'\b' + pattern + r'\b', text):
                return level
    
    # Default to Bachelor's if nothing found
    return "Bachelor's"

def extract_experience_years(text):
    """Extract years of experience from resume text using regex"""
    # Look for patterns like "X years of experience" or "X+ years"
    patterns = [
        r'(\d+)\+?\s*years?\s*(?:of)?\s*experience',
        r'experience\s*(?:of)?\s*(\d+)\+?\s*years?',
        r'worked\s*(?:for)?\s*(\d+)\+?\s*years?'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text.lower())
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                pass
    
    # If no explicit mention, try to estimate from work history
    # Count the number of job positions by looking for common job title indicators
    job_title_indicators = [
        r'senior', r'junior', r'lead', r'manager', r'director', r'vp', r'chief',
        r'engineer', r'developer', r'analyst', r'specialist', r'consultant',
        r'coordinator', r'associate', r'assistant', r'head', r'supervisor'
    ]
    
    job_count = 0
    for indicator in job_title_indicators:
        matches = re.findall(r'\b' + indicator + r'\b', text.lower())
        job_count += len(matches)
    
    # Assume average of 2 years per position
    if job_count > 0:
        return min(job_count, 15)  # Cap at 15 years
    
    return 2  # Default to 2 years if nothing found

def extract_role(text):
    """Extract job role from resume text using regex"""
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

def extract_summary(text, max_length=150):
    """Generate a summary from resume text"""
    # Try to find an objective or summary section
    text_lower = text.lower()
    
    # Look for common summary section headers
    summary_headers = [
        "professional summary", "summary", "profile", "objective", "about me", 
        "career objective", "professional profile"
    ]
    
    # Try to find a summary section
    summary = ""
    lines = text.split('\n')
    
    # First approach: Look for summary headers
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        if any(header in line_lower for header in summary_headers):
            # Found a summary header, extract the next few lines
            summary_lines = []
            for j in range(i+1, min(i+5, len(lines))):
                if lines[j].strip() and len(lines[j].strip()) > 10:
                    summary_lines.append(lines[j].strip())
                elif summary_lines:  # Stop if we've already found some content and hit an empty line
                    break
            
            if summary_lines:
                summary = " ".join(summary_lines)
                break
    
    # Second approach: Use the first paragraph if no summary found
    if not summary:
        paragraph = []
        for line in lines[:10]:  # Look in first 10 lines
            if line.strip() and len(line.strip()) > 10:
                paragraph.append(line.strip())
            elif paragraph:  # Stop if we've already found some content and hit an empty line
                break
        
        if paragraph:
            summary = " ".join(paragraph)
    
    # Truncate if too long
    if len(summary) > max_length:
        summary = summary[:max_length].rsplit(' ', 1)[0] + "..."
    
    # If still no summary, create a generic one
    if not summary:
        role = extract_role(text)
        skills = extract_skills(text)
        experience = extract_experience_years(text)
        summary = f"{role} with {experience} years of experience in {', '.join(skills[:3])}."
    
    return summary

def analyze_resume(resume_text):
    """Analyze a resume using regex extraction"""
    try:
        logger.info("Analyzing resume with regex extraction")
        
        # Extract information
        name = extract_name(resume_text)
        email = extract_email(resume_text)
        phone = extract_phone(resume_text)
        skills = extract_skills(resume_text)
        education_level = extract_education(resume_text)
        experience_years = extract_experience_years(resume_text)
        role = extract_role(resume_text)
        summary = extract_summary(resume_text)
        
        # Create analysis result
        analysis = {
            "name": name,
            "email": email,
            "phone": phone,
            "summary": summary,
            "skills": skills,
            "experience_years": experience_years,
            "education_level": education_level,
            "role": role
        }
        
        logger.info(f"Successfully analyzed resume: {name}")
        return analysis
        
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        # Return a default analysis
        return {
            "name": "Unknown",
            "email": "Unknown",
            "phone": "Unknown",
            "summary": "Professional with relevant experience.",
            "skills": ["Communication", "Problem Solving", "Teamwork"],
            "experience_years": 2,
            "education_level": "Bachelor's",
            "role": "Professional"
        }

def generate_embedding(text):
    """Generate a simple embedding for text using word frequencies"""
    # Create a simple word frequency vector
    # This is a very basic approach, but it's fast and doesn't require external dependencies
    words = re.findall(r'\b\w+\b', text.lower())
    word_freq = {}
    
    # Count word frequencies
    for word in words:
        if len(word) > 2:  # Skip very short words
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Create a simple embedding (just the word frequencies)
    return word_freq

def search_resumes(query, filters=None):
    """Search for resumes matching a query"""
    try:
        logger.info(f"Searching resumes with query: {query}")
        
        # Generate query embedding (word frequencies)
        query_embedding = generate_embedding(query)
        
        # Calculate scores for each resume
        results = []
        for resume in resumes:
            # Skip if no embedding
            if not resume.get("embedding"):
                continue
            
            # Calculate similarity score using word overlap
            resume_embedding = resume["embedding"]
            
            # Find common words
            common_words = set(query_embedding.keys()) & set(resume_embedding.keys())
            
            # Calculate score based on common words and their frequencies
            score = 0
            for word in common_words:
                score += min(query_embedding[word], resume_embedding[word])
            
            # Apply filters if provided
            if filters:
                # Filter by minimum experience
                if "min_experience" in filters and resume["analysis"]["experience_years"] < filters["min_experience"]:
                    continue
                
                # Filter by education level
                if "education_level" in filters:
                    education_levels = {
                        "PhD": 5,
                        "Master's": 4,
                        "Bachelor's": 3,
                        "Associate's": 2,
                        "High School": 1
                    }
                    
                    required_level = education_levels.get(filters["education_level"], 0)
                    resume_level = education_levels.get(resume["analysis"]["education_level"], 0)
                    
                    if resume_level < required_level:
                        continue
                
                # Filter by skills
                if "skills" in filters and filters["skills"]:
                    required_skills = [s.lower() for s in filters["skills"]]
                    resume_skills = [s.lower() for s in resume["analysis"]["skills"]]
                    
                    # Check if resume has at least one of the required skills
                    if not any(skill in resume_skills for skill in required_skills):
                        continue
            
            # Add to results if score is positive
            if score > 0:
                results.append({
                    "id": resume["id"],
                    "filename": resume["filename"],
                    "name": resume["analysis"]["name"],
                    "summary": resume["analysis"]["summary"],
                    "skills": resume["analysis"]["skills"],
                    "experience_years": resume["analysis"]["experience_years"],
                    "education_level": resume["analysis"]["education_level"],
                    "role": resume["analysis"]["role"],
                    "score": score,
                    "upload_date": resume["upload_date"],
                    "download_url": f"/api/resumes/download/{resume['id']}"
                })
        
        # Sort by score (descending)
        results.sort(key=lambda x: x["score"], reverse=True)
        
        logger.info(f"Found {len(results)} matching resumes")
        return results
        
    except Exception as e:
        logger.error(f"Error searching resumes: {str(e)}")
        return []

# API Routes
@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {
        "status": "ok",
        "message": "ResuMatch Regex-Based API is running",
        "docs_url": "/docs"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.0.0"
    }

@app.post("/api/resumes/upload", response_model=ResumeResponse)
async def upload_resume(file: UploadFile = File(...), metadata: str = Form(None)):
    """Upload a resume file"""
    try:
        logger.info(f"Received resume upload: {file.filename}")
        
        # Check if file is a PDF
        if not file.filename.lower().endswith('.pdf'):
            logger.warning(f"Invalid file type: {file.filename}")
            return JSONResponse(
                status_code=400,
                content={"message": "Only PDF files are supported"}
            )
        
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
            return JSONResponse(
                status_code=500,
                content={"message": f"Error saving file: {str(e)}"}
            )
        
        # Extract text from PDF
        resume_text = extract_text_from_pdf(file_path)
        
        # If we couldn't extract any text, return an error
        if resume_text.startswith("Error") or resume_text.startswith("No text") or resume_text.startswith("Unable"):
            return JSONResponse(
                status_code=400,
                content={"message": resume_text}
            )
        
        # Parse metadata if provided
        meta = {}
        if metadata:
            try:
                meta = json.loads(metadata)
            except:
                logger.warning(f"Invalid metadata: {metadata}")
        
        # Analyze the resume
        analysis = analyze_resume(resume_text)
        
        # Generate embedding
        embedding = generate_embedding(resume_text)
        
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
        resumes.append(resume)
        
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
        return JSONResponse(
            status_code=500,
            content={"message": f"Error processing resume: {str(e)}"}
        )

@app.post("/api/resumes/upload-bulk")
async def upload_bulk_resumes(files: List[UploadFile] = File(...)):
    """Upload multiple resume files"""
    try:
        logger.info(f"Received bulk resume upload: {len(files)} files")
        
        results = []
        for file in files:
            try:
                # Process each file
                result = await upload_resume(file)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing file {file.filename}: {str(e)}")
                results.append({
                    "filename": file.filename,
                    "error": str(e)
                })
        
        return {
            "message": f"Processed {len(results)} files",
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error processing bulk upload: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error processing bulk upload: {str(e)}"}
        )

@app.get("/api/resumes")
async def get_all_resumes():
    """Get all resumes"""
    try:
        logger.info("Getting all resumes")
        
        # Return all resumes (without the full text and embedding)
        results = []
        for resume in resumes:
            results.append({
                "id": resume["id"],
                "filename": resume["filename"],
                "name": resume["analysis"]["name"],
                "summary": resume["analysis"]["summary"],
                "skills": resume["analysis"]["skills"],
                "experience_years": resume["analysis"]["experience_years"],
                "education_level": resume["analysis"]["education_level"],
                "role": resume["analysis"]["role"],
                "upload_date": resume["upload_date"],
                "download_url": f"/api/resumes/download/{resume['id']}"
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error getting all resumes: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error getting all resumes: {str(e)}"}
        )

@app.post("/api/resumes/search")
async def search(query: SearchQuery):
    """Search for resumes matching a query"""
    try:
        logger.info(f"Searching resumes with query: {query.query}")
        
        # Search for matching resumes
        results = search_resumes(query.query, query.filters)
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching resumes: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error searching resumes: {str(e)}"}
        )

@app.get("/api/resumes/download/{resume_id}")
async def download_resume(resume_id: str):
    """Download a resume file"""
    try:
        logger.info(f"Downloading resume: {resume_id}")
        
        # Find the resume
        resume = next((r for r in resumes if r["id"] == resume_id), None)
        if not resume:
            return JSONResponse(
                status_code=404,
                content={"message": f"Resume not found: {resume_id}"}
            )
        
        # Return the file
        return FileResponse(
            resume["file_path"],
            filename=resume["filename"],
            media_type="application/pdf"
        )
        
    except Exception as e:
        logger.error(f"Error downloading resume: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error downloading resume: {str(e)}"}
        )

@app.get("/api/skills")
async def get_all_skills():
    """Get all skills from all resumes"""
    try:
        logger.info("Getting all skills")
        
        # Collect all skills
        all_skills = set()
        for resume in resumes:
            all_skills.update(resume["analysis"]["skills"])
        
        # Sort and return
        return sorted(list(all_skills))
        
    except Exception as e:
        logger.error(f"Error getting all skills: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error getting all skills: {str(e)}"}
        )

@app.post("/resumes/analyze")
async def analyze_resume_text(data: Dict[str, Any] = Body(...)):
    """Analyze resume text"""
    try:
        logger.info("Received resume text analysis request")
        
        # Get the resume text
        resume_text = data.get("text", "")
        if not resume_text:
            return JSONResponse(
                status_code=400,
                content={"message": "No resume text provided"}
            )
        
        # Analyze the resume
        analysis = analyze_resume(resume_text)
        
        return {
            "analysis": analysis
        }
        
    except Exception as e:
        logger.error(f"Error analyzing resume text: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"message": f"Error analyzing resume text: {str(e)}"}
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event"""
    try:
        logger.info("Starting up ResuMatch Regex-Based API")
        
        # Create upload directory if it doesn't exist
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        logger.info(f"Upload directory created at {UPLOAD_DIR}")
        
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("regex-backend:app", host="0.0.0.0", port=8002, reload=True)
