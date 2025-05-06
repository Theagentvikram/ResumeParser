#!/usr/bin/env python3
"""
Test script to analyze a resume with a timeout and fallback mechanisms
"""
import os
import sys
import json
import time
import signal
import logging
import tempfile
import shutil
from pathlib import Path
import fitz  # PyMuPDF

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if llama-cpp is available
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
    logger.info("llama_cpp is available for local LLM inference")
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.error("llama_cpp is not available. Please install it with: pip install llama-cpp-python")
    sys.exit(1)

# Path to the Mistral model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "backend", "models", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
if not os.path.exists(MODEL_PATH):
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "backend", "models", "llama-2-7b-chat.Q4_K_M.gguf")
    if not os.path.exists(MODEL_PATH):
        logger.error(f"No model found. Please ensure either Mistral or Llama model is available.")
        sys.exit(1)

logger.info(f"Using model: {MODEL_PATH}")

# Global LLM instance
llm = None

def init_llm():
    """Initialize the LLM"""
    global llm
    
    if llm is not None:
        return llm
    
    try:
        logger.info(f"Loading model from {MODEL_PATH}")
        
        llm = Llama(
            model_path=MODEL_PATH,
            n_ctx=2048,  # Reduced context size for faster processing
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
        
        logger.info(f"Extracted {len(text)} characters from PDF")
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise Exception(f"Failed to extract text from PDF: {str(e)}")

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

def analyze_resume_with_timeout(resume_text, timeout_seconds=10):
    """Analyze a resume with a timeout"""
    try:
        # Initialize the LLM
        model = init_llm()
        
        # Truncate text if it's too long
        max_chars = 1500  # Reduced for faster processing
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
        
        # Set up timeout handler
        class TimeoutException(Exception):
            pass
        
        def timeout_handler(signum, frame):
            raise TimeoutException("Analysis timed out")
        
        # Set the timeout
        original_handler = signal.getsignal(signal.SIGALRM)
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout_seconds)
        
        try:
            # Generate completion
            start_time = time.time()
            response = model(
                prompt,
                max_tokens=256,
                temperature=0.1,
                top_p=0.95,
                stop=["</s>", "[/INST]"]
            )
            end_time = time.time()
            
            # Extract generated text
            generated_text = response["choices"][0]["text"] if "choices" in response else ""
            
            logger.info(f"LLM response generated in {end_time - start_time:.2f} seconds")
            
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
                return analysis_result, False  # Second value indicates if fallback was used
                
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing response as JSON: {str(e)}")
                logger.debug(f"Raw response: {generated_text[:200]}...")
                raise
                
        except TimeoutException:
            logger.warning(f"Analysis timed out after {timeout_seconds} seconds")
            raise
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {str(e)}")
            raise
            
    except (TimeoutException, json.JSONDecodeError, Exception) as e:
        # Use fallback analysis
        logger.info("Using fallback analysis methods")
        return {
            "name": extract_name(resume_text),
            "summary": "Professional with relevant experience.",
            "skills": extract_skills(resume_text),
            "experience_years": estimate_experience(resume_text),
            "education_level": extract_education(resume_text),
            "role": extract_role(resume_text)
        }, True  # Second value indicates fallback was used
    finally:
        # Reset the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)

def main():
    """Main function"""
    if len(sys.argv) < 2:
        logger.error("Please provide a path to a PDF resume file")
        print("Usage: python test-resume-analysis.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        logger.error(f"File not found: {pdf_path}")
        sys.exit(1)
    
    try:
        # Extract text from PDF
        resume_text = extract_text_from_pdf(pdf_path)
        
        # Analyze resume with timeout
        print("\nAnalyzing resume...")
        start_time = time.time()
        
        # Try with different timeout values if needed
        for timeout in [5, 10, 15]:
            try:
                result, used_fallback = analyze_resume_with_timeout(resume_text, timeout)
                end_time = time.time()
                
                print(f"\nAnalysis completed in {end_time - start_time:.2f} seconds")
                if used_fallback:
                    print("Note: Used fallback analysis methods due to timeout or parsing error")
                
                print("\nAnalysis Result:")
                print(json.dumps(result, indent=2))
                
                return
            except Exception as e:
                logger.warning(f"Analysis with {timeout}s timeout failed: {str(e)}")
                print(f"Trying with longer timeout...")
        
        # If all timeouts failed, use pure fallback
        print("\nUsing pure fallback analysis...")
        result = {
            "name": extract_name(resume_text),
            "summary": "Professional with relevant experience.",
            "skills": extract_skills(resume_text),
            "experience_years": estimate_experience(resume_text),
            "education_level": extract_education(resume_text),
            "role": extract_role(resume_text)
        }
        
        print("\nFallback Analysis Result:")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
