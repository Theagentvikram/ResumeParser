import os
import json
import requests
import logging
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import re

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API token from environment
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")

# Mistral API URL
MISTRAL_API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"

def analyze_resume_with_mistral(resume_text: str) -> Dict[str, Any]:
    """
    Analyze a resume using the Mistral API through Hugging Face
    """
    logger.info("Starting Mistral API resume analysis")
    
    if not HUGGINGFACE_API_TOKEN:
        raise ValueError("Hugging Face API token not found. Please set the HUGGINGFACE_API_TOKEN environment variable.")
    
    # Clean and truncate text if needed
    # Mistral models typically have a context window of about 8k tokens
    # Truncate to ~6000 characters to be safe
    max_chars = 6000
    if len(resume_text) > max_chars:
        logger.info(f"Truncating resume text from {len(resume_text)} to {max_chars} characters")
        resume_text = resume_text[:max_chars]
    
    # Create a structured prompt for better extraction
    prompt = f"""You are an AI assistant that specializes in resume analysis. Analyze the following resume text and extract key information.
    
RESUME TEXT:
{resume_text}

Based on the resume above, extract and return ONLY the following information in JSON format:

1. summary: A professional summary of the candidate (3-4 sentences)
2. skills: An array of professional skills mentioned in the resume (technical, soft skills, tools, etc.)
3. experience: The years of professional experience (as a number)
4. educationLevel: The highest level of education (High School, Associate's, Bachelor's, Master's, PhD, or Other)
5. category: The job category that best matches this resume (e.g., Software Engineering, Data Science, Marketing, etc.)

Format your response as a valid JSON object with these five keys. DO NOT include any explanations before or after the JSON.
Example response format:
{{
  "summary": "Professional summary here...",
  "skills": ["Skill 1", "Skill 2", "Skill 3"],
  "experience": 5,
  "educationLevel": "Bachelor's",
  "category": "Software Engineering" 
}}
"""

    # API endpoint
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
    
    # Set up the headers with authentication
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Prepare the payload
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.1,
            "top_p": 0.95,
            "do_sample": True
        }
    }
    
    try:
        # Make the API call
        logger.info("Sending request to Hugging Face API")
        response = requests.post(API_URL, headers=headers, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
            result = response.json()
            logger.info("Received successful response from Hugging Face API")
            
            # Extract the generated text
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "")
                
                # Extract JSON from the response
                # Find the start and end of JSON (it might be surrounded by other text)
                try:
                    # Find the first opening brace
                    json_start = generated_text.find("{")
                    if json_start == -1:
                        raise ValueError("No JSON object found in the response")
                    
                    # Find the matching closing brace
                    json_end = generated_text.rfind("}")
                    if json_end == -1:
                        raise ValueError("No closing brace found in the response")
                    
                    # Extract the JSON string
                    json_str = generated_text[json_start:json_end+1]
                    
                    # Parse the JSON
                    analysis_result = json.loads(json_str)
                    
                    # Validate the result has all required fields
                    required_fields = ["summary", "skills", "experience", "educationLevel", "category"]
                    missing_fields = [field for field in required_fields if field not in analysis_result]
                    
                    if missing_fields:
                        # Provide defaults for missing fields
                        for field in missing_fields:
                            if field == "skills":
                                analysis_result[field] = []
                            elif field == "experience":
                                analysis_result[field] = 0
                            else:
                                analysis_result[field] = "Not found"
                        
                        logger.warning(f"Missing fields in analysis result: {missing_fields}. Added defaults.")
                    
                    # Ensure skills is a list
                    if not isinstance(analysis_result["skills"], list):
                        if isinstance(analysis_result["skills"], str):
                            # Split by commas if it's a string
                            analysis_result["skills"] = [skill.strip() for skill in analysis_result["skills"].split(",")]
                        else:
                            analysis_result["skills"] = []
                    
                    # Ensure experience is a number
                    if not isinstance(analysis_result["experience"], (int, float)):
                        try:
                            analysis_result["experience"] = int(analysis_result["experience"])
                        except (ValueError, TypeError):
                            analysis_result["experience"] = 0
                    
                    logger.info(f"Successfully extracted {len(analysis_result['skills'])} skills")
                    return analysis_result
                
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from response: {e}")
                    logger.debug(f"Raw response: {generated_text}")
                    raise ValueError(f"Failed to parse analysis result: {e}")
            else:
                logger.error("Unexpected response format from Hugging Face API")
                raise ValueError("Received unexpected response format from Hugging Face API")
        
        elif response.status_code == 401:
            logger.error("Authentication failed with Hugging Face API (401)")
            raise ValueError("Authentication failed with Hugging Face API. Please check your API token.")
        
        elif response.status_code == 503:
            logger.error("Hugging Face API service unavailable (503)")
            raise ValueError("Hugging Face API service is currently unavailable. Please try again later.")
        
        else:
            logger.error(f"API call failed with status code {response.status_code}: {response.text}")
            raise ValueError(f"API call failed with status code {response.status_code}: {response.text}")
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to Hugging Face API failed: {e}")
        raise ValueError(f"Failed to connect to Hugging Face API: {e}")
    
    except Exception as e:
        logger.error(f"Unexpected error in resume analysis: {e}")
        raise ValueError(f"Resume analysis failed: {e}")

def get_huggingface_model_status():
    """
    Check if the Hugging Face API and model are available
    Returns a dictionary with status information
    """
    if not HUGGINGFACE_API_TOKEN:
        return {
            "status": "unavailable",
            "message": "No Hugging Face API token found in environment variables. Please set HUGGINGFACE_API_TOKEN in your .env file.",
            "using_fallback": True
        }
    
    try:
        # Simple API health check
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}"}
        response = requests.get(
            "https://api-inference.huggingface.co/status/mistralai/Mistral-7B-Instruct-v0.2", 
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "status": "available",
                "message": "Hugging Face API and Mistral-7B model are available",
                "using_fallback": False
            }
        else:
            return {
                "status": "error",
                "message": f"Hugging Face API returned status code {response.status_code}: {response.text}",
                "using_fallback": True
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking Hugging Face API status: {str(e)}",
            "using_fallback": True
        } 