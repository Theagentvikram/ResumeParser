import os
import json
import requests
import logging
import re
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# OpenRouter API settings - load from environment but with fallbacks
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")

# Log the API key being used (first 10 chars and last 5 chars only for security)
logger.info(f"Using OpenRouter API key: {OPENROUTER_API_KEY[:10]}...{OPENROUTER_API_KEY[-5:]}")
logger.info(f"API key length: {len(OPENROUTER_API_KEY)} characters")


def analyze_resume_with_openrouter(resume_text: str) -> Dict[str, Any]:
    """
    Analyze a resume using the OpenRouter API with Mistral model
    """
    logger.info("Starting OpenRouter API resume analysis with Mistral model")
    
    # Clean and truncate text if needed
    # Truncate to ~6000 characters to be safe
    max_chars = 6000
    if len(resume_text) > max_chars:
        logger.info(f"Truncating resume text from {len(resume_text)} to {max_chars} characters")
        resume_text = resume_text[:max_chars]
    
    # Create a structured prompt for better extraction
    system_prompt = """You are an expert AI resume analyzer with years of experience in HR and recruitment. 
    Your task is to carefully analyze resumes and extract accurate, detailed information about the candidate's skills, 
    experience, education, and professional background. Be thorough, precise, and focus on extracting factual information 
    directly from the resume text without making assumptions or adding information not present in the resume.
    
    When analyzing skills, identify both technical and soft skills mentioned in the resume.
    When determining years of experience, calculate based on the work history dates provided.
    When identifying education level, look for the highest degree mentioned.
    When determining job category, consider the candidate's most recent roles and overall experience.
    
    Your analysis should be objective, accurate, and based solely on the information provided in the resume."""
    
    user_prompt = f"""Analyze the following resume text and extract key information.

RESUME TEXT:
{resume_text}

Based on the resume above, extract and return ONLY the following information in JSON format:

1. summary: A professional summary of the candidate (3-4 sentences) that highlights their key qualifications, experience, and strengths. Make this detailed and specific to the candidate.

2. skills: An array of ALL professional skills mentioned in the resume, including technical skills, soft skills, tools, programming languages, frameworks, methodologies, etc. Be comprehensive and include everything mentioned.

3. experience: The total years of professional experience as a number (integer). Calculate this based on the work history dates in the resume. If exact dates aren't provided, make a reasonable estimate based on the information available.

4. educationLevel: The highest level of education attained (High School, Associate's, Bachelor's, Master's, PhD, or Other). Look for specific degrees mentioned.

5. category: The job category or industry that best matches this resume based on the candidate's experience and skills (e.g., Software Engineering, Data Science, Marketing, Finance, Healthcare, etc.). Be specific.

Format your response as a valid JSON object with these five keys. DO NOT include any explanations before or after the JSON. Ensure the JSON is properly formatted and valid."""
    
    # Set up the headers with authentication
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://resumatch.app",  # Replace with your actual domain
        "X-Title": "ResuMatch",  # Your app name
        "OpenAI-Organization": "org-",  # Required for OpenRouter
        "User-Agent": "ResuMatch/1.0"  # Helpful for debugging
    }
    
    # Prepare the payload
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.1,
        "top_p": 0.95
    }
    
    try:
        # Make the API call
        logger.info(f"Sending request to OpenRouter API with model: {OPENROUTER_MODEL}")
        logger.info(f"API URL: {OPENROUTER_API_URL}")
        logger.info(f"API Key (first 10 chars): {OPENROUTER_API_KEY[:10]}...")
        logger.info(f"Headers: {headers}")
        logger.info(f"Payload: {json.dumps(payload)[:500]}...")
        
        # Set a timeout to avoid hanging indefinitely
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=30)
        
        # Log the response status and headers
        logger.info(f"Response status code: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        # Handle different response status codes
        if response.status_code == 200:
            # Success! Parse the response
            result = response.json()
            logger.info("Received successful response from OpenRouter API")
            
            # Extract the generated text
            if "choices" in result and len(result["choices"]) > 0:
                generated_text = result["choices"][0]["message"]["content"]
                
                # Clean up any markdown formatting (```json)
                if "```json" in generated_text or "```" in generated_text:
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', generated_text)
                    if json_match:
                        generated_text = json_match.group(1).strip()
                
                # Clean up any other potential formatting issues
                if not generated_text.strip().startswith("{"):
                    # If it doesn't start with {, try to find JSON within the text
                    json_start = generated_text.find("{")
                    json_end = generated_text.rfind("}")
                    if json_start >= 0 and json_end > json_start:
                        generated_text = generated_text[json_start:json_end+1]
                
                logger.info(f"Cleaned JSON text: {generated_text[:100]}...")
                
                try:
                    # Parse the JSON
                    parsed_result = json.loads(generated_text)
                    
                    # Validate that we have all the required fields
                    required_fields = ["summary", "skills", "experience", "educationLevel", "category"]
                    for field in required_fields:
                        if field not in parsed_result:
                            logger.warning(f"Missing required field in response: {field}")
                            parsed_result[field] = "" if field != "skills" else [] if field == "skills" else 0 if field == "experience" else ""
                    
                    # Ensure skills is a list
                    if not isinstance(parsed_result["skills"], list):
                        parsed_result["skills"] = [s.strip() for s in str(parsed_result["skills"]).split(",")]
                    
                    # Ensure experience is a number
                    if not isinstance(parsed_result["experience"], (int, float)):
                        try:
                            parsed_result["experience"] = int(str(parsed_result["experience"]).strip())
                        except:
                            parsed_result["experience"] = 0
                    
                    # Standardize educationLevel to match expected values
                    edu_level = parsed_result["educationLevel"].lower()
                    if "master" in edu_level:
                        parsed_result["educationLevel"] = "Master's"
                    elif "bachelor" in edu_level or "bs" in edu_level or "ba" in edu_level:
                        parsed_result["educationLevel"] = "Bachelor's"
                    elif "phd" in edu_level or "doctor" in edu_level:
                        parsed_result["educationLevel"] = "PhD"
                    elif "associate" in edu_level:
                        parsed_result["educationLevel"] = "Associate's"
                    elif "high school" in edu_level:
                        parsed_result["educationLevel"] = "High School"
                    
                    logger.info(f"Successfully extracted {len(parsed_result.get('skills', []))} skills")
                    return parsed_result
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from response: {e}")
                    logger.debug(f"Raw response: {generated_text}")
                    raise ValueError(f"Failed to parse analysis result: {e}")
            else:
                logger.error("Unexpected response format from OpenRouter API")
                raise ValueError("Received unexpected response format from OpenRouter API")
        
        elif response.status_code == 401:
            logger.error(f"Authentication failed with OpenRouter API (401): {response.text}")
            # Check if the API key is properly formatted
            if not OPENROUTER_API_KEY.startswith('sk-or-v1-'):
                logger.error(f"API key format appears incorrect: {OPENROUTER_API_KEY[:10]}...")
                raise ValueError("Authentication failed: API key format appears incorrect. It should start with 'sk-or-v1-'.")
            else:
                raise ValueError("Authentication failed with OpenRouter API. Please check your API key or try regenerating it.")
        
        elif response.status_code == 403:
            logger.error(f"Permission denied by OpenRouter API (403): {response.text}")
            raise ValueError("Permission denied by OpenRouter API. Your API key might not have access to the requested model.")
        
        elif response.status_code == 429:
            logger.error(f"Rate limit exceeded on OpenRouter API (429): {response.text}")
            raise ValueError("Rate limit exceeded on OpenRouter API. Please try again later or reduce the frequency of requests.")
        
        elif response.status_code == 503:
            logger.error(f"OpenRouter API service unavailable (503): {response.text}")
            raise ValueError("OpenRouter API service is currently unavailable. Please try again later.")
        
        else:
            logger.error(f"API call failed with status code {response.status_code}: {response.text}")
            raise ValueError(f"API call failed with status code {response.status_code}: {response.text}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to OpenRouter API failed: {e}")
        raise ValueError(f"Failed to connect to OpenRouter API: {e}")
    
    except Exception as e:
        logger.error(f"Unexpected error in resume analysis: {e}")
        raise ValueError(f"Resume analysis failed: {e}")


def get_openrouter_model_status() -> Dict[str, Any]:
    """
    Check if the OpenRouter API and model are available
    """
    try:
        # Set up the headers with authentication
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://resumatch.app",  # Replace with your actual domain
            "X-Title": "ResuMatch",  # Your app name
            "OpenAI-Organization": "org-",  # Required for OpenRouter
            "User-Agent": "ResuMatch/1.0"  # Helpful for debugging
        }
        
        # Use the models endpoint to check API status
        models_url = "https://openrouter.ai/api/v1/models"
        
        logger.info("Checking OpenRouter API status")
        response = requests.get(models_url, headers=headers)
        
        logger.info(f"OpenRouter API status check: {response.status_code}")
        
        if response.status_code == 200:
            # API is accessible, check if our model is available
            models_data = response.json()
            available_models = [model.get("id") for model in models_data.get("data", [])]
            
            # Log available free models for debugging
            free_models = [model for model in available_models if "free" in model.lower()]
            logger.info(f"Available free models: {free_models}")
            
            # Check if our model is available (case insensitive)
            model_found = False
            for model in available_models:
                if model.lower() == OPENROUTER_MODEL.lower():
                    model_found = True
                    break
            
            if model_found:
                return {
                    "status": "available",
                    "message": "OpenRouter API and model are available",
                    "using_fallback": False,
                    "mode": "api"
                }
            else:
                # Model not found in available models, but we'll try anyway
                # since the model list might not be complete
                logger.warning(f"Model {OPENROUTER_MODEL} not found in available models list, but will try to use it anyway")
                return {
                    "status": "available",
                    "message": f"OpenRouter API is available, proceeding with {OPENROUTER_MODEL}",
                    "using_fallback": False,
                    "mode": "api"
                }
        elif response.status_code == 401:
            logger.error(f"Authentication failed with OpenRouter API (401): {response.text}")
            return {
                "status": "error",
                "message": f"OpenRouter API returned status code 401: {response.text}",
                "using_fallback": True,
                "mode": "fallback"
            }
        else:
            logger.error(f"OpenRouter API returned status code {response.status_code}: {response.text}")
            return {
                "status": "error",
                "message": f"OpenRouter API returned status code {response.status_code}: {response.text}",
                "using_fallback": True,
                "mode": "fallback"
            }
    except Exception as e:
        logger.error(f"Error checking OpenRouter API status: {e}")
        return {
            "status": "error",
            "message": f"Error checking OpenRouter API status: {e}",
            "using_fallback": True,
            "mode": "fallback"
        }
