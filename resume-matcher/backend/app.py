#!/usr/bin/env python3
"""
Resume Matcher - FastAPI Backend
Simple and reliable implementation with regex extraction and optional LLM integration
"""
import os
import re
import json
import uuid
import logging
import requests
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import fitz  # PyMuPDF
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("resume-matcher")

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "data", "uploads")
SUMMARIES_DIR = os.path.join(BASE_DIR, "data", "summaries")
DB_DIR = os.path.join(BASE_DIR, "data", "db")

# OpenRouter API settings
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free"

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(SUMMARIES_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# In-memory database (will be saved to JSON)
resumes_db = []
skills_db = set()

# Initialize TF-IDF Vectorizer for text similarity
vectorizer = TfidfVectorizer(stop_words='english')

# Create FastAPI app
app = FastAPI(title="Resume Matcher API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def extract_text_from_pdf(file_path):
    """Extract text from a PDF file"""
    try:
        logger.info(f"Extracting text from PDF: {file_path}")
        
        # Open the PDF
        doc = fitz.open(file_path)
        
        # Extract text from each page (limit to first 5 pages for speed)
        text = ""
        for page_num in range(min(5, len(doc))):
            page = doc.load_page(page_num)
            text += page.get_text()
        
        # Close the document
        doc.close()
        
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return None

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
    text = text.lower()
    
    # Look for explicit mentions of years of experience
    exp_patterns = [
        r'(\d+)(?:\+)?\s*(?:years|yrs)(?:\s*of)?\s*experience',
        r'experience\s*(?:of|:)?\s*(\d+)(?:\+)?\s*(?:years|yrs)',
        r'(?:over|more than)\s*(\d+)\s*(?:years|yrs)(?:\s*of)?\s*experience'
    ]
    
    for pattern in exp_patterns:
        matches = re.findall(pattern, text)
        if matches:
            return max(map(int, matches))
    
    # If no explicit mention, try to calculate from work history
    # Look for date ranges like "2018-2022" or "2018-present"
    date_ranges = re.findall(r'(\d{4})\s*[-–—]\s*(\d{4}|present|current|now)', text, re.IGNORECASE)
    
    if date_ranges:
        total_years = 0
        current_year = datetime.now().year
        
        for start, end in date_ranges:
            start_year = int(start)
            end_year = current_year if end.lower() in ['present', 'current', 'now'] else int(end)
            total_years += end_year - start_year
        
        return total_years
    
    # Default to 2 years if nothing found
    return 2

def extract_role(text):
    """Extract job role from resume text using regex"""
    text = text.lower()
    
    # Common job titles
    job_titles = [
        "software engineer", "software developer", "web developer", "frontend developer", "backend developer",
        "full stack developer", "data scientist", "data analyst", "data engineer", "machine learning engineer",
        "devops engineer", "cloud engineer", "site reliability engineer", "product manager", "project manager",
        "ux designer", "ui designer", "graphic designer", "marketing manager", "sales manager",
        "business analyst", "financial analyst", "accountant", "human resources", "customer support"
    ]
    
    # Look for job titles in text
    for title in job_titles:
        if re.search(r'\b' + re.escape(title) + r'\b', text):
            return title.title()  # Capitalize title
    
    # If no specific title found, try to extract from experience section
    experience_section = re.search(r'(?:experience|employment|work history)(.*?)(?:education|skills|projects|references|$)', text, re.DOTALL | re.IGNORECASE)
    
    if experience_section:
        # Look for patterns like "Job Title at Company" or "Job Title, Company"
        job_matches = re.findall(r'([A-Za-z\s]+)(?:\sat\s|,\s)([A-Za-z\s]+)', experience_section.group(1))
        if job_matches:
            return job_matches[0][0].strip().title()
    
    # Default to a generic role if nothing found
    return "Professional"

def call_openrouter_api(prompt, max_tokens=500):
    """Call the OpenRouter API with the given prompt"""
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": OPENROUTER_MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant that analyzes resumes and extracts relevant information."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens
        }
        
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0]["message"]["content"]
        else:
            logger.error(f"Unexpected API response format: {result}")
            return None
    except Exception as e:
        logger.error(f"Error calling OpenRouter API: {str(e)}")
        return None

def extract_skills_llm(text):
    """Extract skills from resume text using LLM"""
    prompt = f"""Extract a list of technical skills from the following resume text. 
    Return ONLY the skills as a comma-separated list without any additional text or explanation.
    Resume text:
    {text}
    """
    
    try:
        response = call_openrouter_api(prompt)
        if response:
            # Clean up the response - remove any explanatory text and just get the skills list
            skills_text = response.strip()
            # Split by commas and clean up each skill
            skills = [skill.strip() for skill in skills_text.split(',')]
            return [skill for skill in skills if skill]  # Filter out empty strings
        else:
            # Fallback to regex extraction if API call fails
            return extract_skills(text)
    except Exception as e:
        logger.error(f"Error extracting skills with LLM: {str(e)}")
        # Fallback to regex extraction
        return extract_skills(text)

def extract_role_llm(text):
    """Extract job role from resume text using LLM"""
    prompt = f"""Extract the most likely current or most recent job role/title from the following resume text.
    Return ONLY the job title without any additional text or explanation.
    Resume text:
    {text}
    """
    
    try:
        response = call_openrouter_api(prompt)
        if response:
            # Clean up the response
            role = response.strip()
            return role
        else:
            # Fallback to regex extraction if API call fails
            return extract_role(text)
    except Exception as e:
        logger.error(f"Error extracting role with LLM: {str(e)}")
        # Fallback to regex extraction
        return extract_role(text)

def extract_experience_years_llm(text):
    """Extract years of experience from resume text using LLM"""
    prompt = f"""Extract the total years of professional experience from the following resume text.
    Return ONLY a number representing the years of experience without any additional text or explanation.
    If you can't determine the exact number, provide your best estimate based on the work history.
    Resume text:
    {text}
    """
    
    try:
        response = call_openrouter_api(prompt)
        if response:
            # Try to extract a number from the response
            match = re.search(r'\d+', response.strip())
            if match:
                return int(match.group())
            else:
                # Fallback to regex extraction if no number found
                return extract_experience_years(text)
        else:
            # Fallback to regex extraction if API call fails
            return extract_experience_years(text)
    except Exception as e:
        logger.error(f"Error extracting experience years with LLM: {str(e)}")
        # Fallback to regex extraction
        return extract_experience_years(text)

def generate_summary_llm(text, max_length=150):
    """Generate a summary from resume text using LLM"""
    prompt = f"""Generate a concise professional summary (maximum 150 characters) for a resume with the following text.
    Focus on highlighting the person's experience level, role, key skills, and education.
    Resume text:
    {text}
    """
    
    try:
        response = call_openrouter_api(prompt)
        if response and len(response.strip()) > 0:
            # Return the summary, truncated if necessary
            return response.strip()[:max_length]
        else:
            # Fallback to rule-based summary if API call fails
            return generate_summary_regex(text, max_length)
    except Exception as e:
        logger.error(f"Error generating summary with LLM: {str(e)}")
        # Fallback to rule-based summary
        return generate_summary_regex(text, max_length)

def generate_summary_regex(text, max_length=150):
    """Generate a simple summary from resume text using regex extraction"""
    # Extract basic information
    name = extract_name(text)
    role = extract_role(text)
    experience_years = extract_experience_years(text)
    education = extract_education(text)
    skills = extract_skills(text)
    
    # Determine experience level
    if experience_years <= 2:
        level = "Junior"
    elif experience_years <= 5:
        level = "Mid-level"
    else:
        level = "Senior"
    
    # Generate summary
    summary = f"{level} {role} with {experience_years} years of experience"
    
    # Add education
    summary += f" and a {education} degree"
    
    # Add skills (up to 3)
    if skills:
        top_skills = skills[:3]
        summary += f". Skilled in {', '.join(top_skills)}"
    
    # Add period at the end if needed
    if not summary.endswith('.'):
        summary += '.'
    
    return summary[:max_length]

def generate_summary(text, max_length=150):
    """Generate a summary from resume text, trying LLM first then falling back to regex"""
    try:
        # Try to generate summary using LLM
        return generate_summary_llm(text, max_length)
    except Exception as e:
        logger.error(f"Error in generate_summary: {str(e)}")
        # Fallback to regex-based summary
        return generate_summary_regex(text, max_length)

def analyze_resume(resume_text):
    """Analyze a resume using LLM with regex extraction as fallback"""
    try:
        # Extract information using a mix of LLM and regex
        name = extract_name(resume_text)
        email = extract_email(resume_text)
        phone = extract_phone(resume_text)
        skills = extract_skills_llm(resume_text)  # Use LLM for better skill extraction
        education = extract_education(resume_text)
        experience_years = extract_experience_years_llm(resume_text)  # Use LLM for better experience extraction
        role = extract_role_llm(resume_text)  # Use LLM for better role extraction
        
        # Generate summary using LLM
        summary = generate_summary(resume_text)
        
        # Add skills to global skills database
        global skills_db
        skills_db.update(skills)
        
        # Determine experience level
        if experience_years <= 2:
            level = "Junior"
        elif experience_years <= 5:
            level = "Mid-level"
        else:
            level = "Senior"
            
        # Determine job category based on skills and role
        tech_keywords = ["software", "developer", "engineer", "web", "frontend", "backend", "fullstack", "programming", "coding"]
        data_keywords = ["data", "analytics", "analysis", "science", "machine learning", "ai", "artificial intelligence", "statistics"]
        design_keywords = ["design", "ui", "ux", "user interface", "user experience", "graphic"]
        
        role_lower = role.lower()
        
        if any(keyword in role_lower for keyword in tech_keywords) or any(skill.lower() in tech_keywords for skill in skills):
            category = "Software Engineering"
        elif any(keyword in role_lower for keyword in data_keywords) or any(skill.lower() in data_keywords for skill in skills):
            category = "Data Science"
        elif any(keyword in role_lower for keyword in design_keywords) or any(skill.lower() in design_keywords for skill in skills):
            category = "Design"
        else:
            category = "Professional"
        
        # Create analysis result
        analysis = {
            "name": name,
            "email": email,
            "phone": phone,
            "skills": skills,
            "education": education,
            "experience_years": experience_years,
            "role": role,
            "level": level,
            "category": category,
            "summary": summary,
            "analyzed_at": datetime.now().isoformat()
        }
        
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        raise

def save_to_db():
    """Save the in-memory database to a JSON file"""
    db_file = os.path.join(DB_DIR, "resumes.json")
    with open(db_file, 'w') as f:
        json.dump(resumes_db, f, indent=2)
    
    skills_file = os.path.join(DB_DIR, "skills.json")
    with open(skills_file, 'w') as f:
        json.dump(list(skills_db), f, indent=2)

def load_from_db():
    """Load the database from JSON files"""
    global resumes_db, skills_db
    
    db_file = os.path.join(DB_DIR, "resumes.json")
    if os.path.exists(db_file):
        with open(db_file, 'r') as f:
            resumes_db = json.load(f)
    
    skills_file = os.path.join(DB_DIR, "skills.json")
    if os.path.exists(skills_file):
        with open(skills_file, 'r') as f:
            skills_db = set(json.load(f))

def search_resumes(query, filters=None):
    """Search for resumes matching a query"""
    if not resumes_db:
        return []
    
    # Apply filters first
    filtered_resumes = resumes_db
    if filters:
        if 'skills' in filters and filters['skills']:
            filtered_resumes = [r for r in filtered_resumes if any(skill in r['analysis']['skills'] for skill in filters['skills'])]
        
        if 'category' in filters and filters['category']:
            filtered_resumes = [r for r in filtered_resumes if r['analysis']['category'] == filters['category']]
        
        if 'min_experience' in filters and filters['min_experience']:
            min_exp = int(filters['min_experience'])
            filtered_resumes = [r for r in filtered_resumes if r['analysis']['experience_years'] >= min_exp]
        
        if 'max_experience' in filters and filters['max_experience']:
            max_exp = int(filters['max_experience'])
            filtered_resumes = [r for r in filtered_resumes if r['analysis']['experience_years'] <= max_exp]
    
    if not filtered_resumes:
        return []
    
    # Prepare documents for TF-IDF
    documents = []
    for resume in filtered_resumes:
        doc = resume['analysis']['summary'] + " " + " ".join(resume['analysis']['skills'])
        documents.append(doc)
    
    # Add the query as the last document
    documents.append(query)
    
    # Create TF-IDF matrix
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    # Get the query vector (last row in the matrix)
    query_vector = tfidf_matrix[-1]
    
    # Calculate cosine similarity between query and each resume
    similarities = cosine_similarity(query_vector, tfidf_matrix[:-1]).flatten()
    
    # Create result with similarity scores
    results = []
    for i, score in enumerate(similarities):
        resume = filtered_resumes[i]
        results.append({
            "resume_id": resume['id'],
            "name": resume['analysis']['name'],
            "summary": resume['analysis']['summary'],
            "skills": resume['analysis']['skills'],
            "category": resume['analysis']['category'],
            "experience_years": resume['analysis']['experience_years'],
            "level": resume['analysis']['level'],
            "similarity_score": float(score)
        })
    
    # Sort by similarity score (descending)
    results.sort(key=lambda x: x['similarity_score'], reverse=True)
    
    # Return top 5 results
    return results[:5]

# API Routes
@app.get("/")
async def root():
    """Root endpoint for health check"""
    return {"message": "Resume Matcher API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "resume_count": len(resumes_db),
        "skills_count": len(skills_db)
    }

@app.post("/resumes/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload a resume file"""
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
        
        # Extract text from PDF
        resume_text = extract_text_from_pdf(file_path)
        
        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract text from the PDF file")
        
        # Analyze resume
        analysis = analyze_resume(resume_text)
        
        # Save summary to file
        summary_file = os.path.join(SUMMARIES_DIR, f"{resume_id}_summary.json")
        with open(summary_file, "w") as f:
            json.dump(analysis, f, indent=2)
        
        # Add to database
        resume_data = {
            "id": resume_id,
            "filename": file.filename,
            "file_path": file_path,
            "upload_date": datetime.now().isoformat(),
            "analysis": analysis
        }
        
        resumes_db.append(resume_data)
        
        # Add skills to skills database
        skills_db.update(analysis["skills"])
        
        # Save to disk
        save_to_db()
        
        return {
            "id": resume_id,
            "filename": file.filename,
            "analysis": analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading resume: {str(e)}")

@app.post("/resumes/upload-bulk")
async def upload_bulk_resumes(files: List[UploadFile] = File(...)):
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
            
            # Extract text from PDF
            resume_text = extract_text_from_pdf(file_path)
            
            if not resume_text:
                logger.warning(f"Could not extract text from {file.filename}")
                continue
            
            # Analyze resume
            analysis = analyze_resume(resume_text)
            
            # Save summary to file
            summary_file = os.path.join(SUMMARIES_DIR, f"{resume_id}_summary.json")
            with open(summary_file, "w") as f:
                json.dump(analysis, f, indent=2)
            
            # Add to database
            resume_data = {
                "id": resume_id,
                "filename": file.filename,
                "file_path": file_path,
                "upload_date": datetime.now().isoformat(),
                "analysis": analysis
            }
            
            resumes_db.append(resume_data)
            
            # Add skills to skills database
            skills_db.update(analysis["skills"])
            
            results.append({
                "id": resume_id,
                "filename": file.filename,
                "name": analysis["name"]
            })
        
        # Save to disk
        save_to_db()
        
        return {
            "message": f"Uploaded {len(results)} resumes successfully",
            "resumes": results
        }
    except Exception as e:
        logger.error(f"Error uploading bulk resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading bulk resumes: {str(e)}")

@app.get("/resumes")
async def get_all_resumes():
    """Get all resumes"""
    try:
        # Format response
        response = []
        for resume in resumes_db:
            response.append({
                "id": resume["id"],
                "name": resume["analysis"]["name"],
                "upload_date": resume["upload_date"],
                "summary": resume["analysis"]["summary"],
                "category": resume["analysis"]["category"],
                "level": resume["analysis"]["level"],
                "skills": resume["analysis"]["skills"],
                "experience_years": resume["analysis"]["experience_years"]
            })
        
        return response
    except Exception as e:
        logger.error(f"Error getting all resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting all resumes: {str(e)}")

@app.post("/resumes/search")
async def search(query: Dict[str, Any] = Body(...)):
    """Search for resumes matching a query"""
    try:
        search_query = query.get("query", "")
        filters = query.get("filters", {})
        
        if not search_query:
            raise HTTPException(status_code=400, detail="Search query is required")
        
        results = search_resumes(search_query, filters)
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching resumes: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching resumes: {str(e)}")

@app.get("/resumes/{resume_id}")
async def get_resume(resume_id: str):
    """Get a specific resume by ID"""
    try:
        resume = next((r for r in resumes_db if r["id"] == resume_id), None)
        
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
        resume = next((r for r in resumes_db if r["id"] == resume_id), None)
        
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
        return {"skills": sorted(list(skills_db))}
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
        
        # Analyze resume
        analysis = analyze_resume(text)
        
        return analysis
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing resume text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing resume text: {str(e)}")

@app.delete("/resumes/{resume_id}")
async def delete_resume(resume_id: str):
    """Delete a resume"""
    try:
        global resumes_db
        resume = next((r for r in resumes_db if r["id"] == resume_id), None)
        
        if not resume:
            raise HTTPException(status_code=404, detail=f"Resume with ID {resume_id} not found")
        
        # Remove from database
        resumes_db = [r for r in resumes_db if r["id"] != resume_id]
        
        # Delete file if it exists
        file_path = resume.get("file_path")
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete summary file if it exists
        summary_file = os.path.join(SUMMARIES_DIR, f"{resume_id}_summary.json")
        if os.path.exists(summary_file):
            os.remove(summary_file)
        
        # Save updated database
        save_to_db()
        
        return {"message": f"Resume with ID {resume_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting resume: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting resume: {str(e)}")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Startup event"""
    logger.info("Starting Resume Matcher API")
    load_from_db()

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    logger.info("Shutting down Resume Matcher API")
    save_to_db()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
