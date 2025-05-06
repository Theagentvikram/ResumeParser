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

# OpenRouter API settings
OPENROUTER_API_KEY = "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"
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "mistralai/mistral-7b-instruct:free"

def analyze_resume_with_openrouter(resume_text: str) -> Dict[str, Any]:
    """
    Analyze a resume using the OpenRouter API with Mistral 7B model
    """
    logger.info("Starting OpenRouter API resume analysis with Mistral 7B")
    
    # Clean and truncate text if needed
    # Truncate to ~6000 characters to be safe
    max_chars = 6000
    if len(resume_text) > max_chars:
        logger.info(f"Truncating resume text from {len(resume_text)} to {max_chars} characters")
        resume_text = resume_text[:max_chars]
    
    # Create a structured prompt for better extraction
    system_prompt = "You are an AI assistant that specializes in resume analysis. Extract key information from resumes accurately."
    
    user_prompt = f"""Analyze the following resume text and extract key information.
    
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
    
    # Set up the headers with authentication
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
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
        logger.info("Sending request to OpenRouter API")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
            result = response.json()
            logger.info("Received successful response from OpenRouter API")
            
            # Extract the generated text
            if "choices" in result and len(result["choices"]) > 0:
                generated_text = result["choices"][0]["message"]["content"]
                
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
                    
                    # Validate the required fields
                    required_fields = ["summary", "skills", "experience", "educationLevel", "category"]
                    for field in required_fields:
                        if field not in analysis_result:
                            analysis_result[field] = "" if field != "skills" else []
                    
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
                logger.error("Unexpected response format from OpenRouter API")
                raise ValueError("Received unexpected response format from OpenRouter API")
        
        elif response.status_code == 401:
            logger.error("Authentication failed with OpenRouter API (401)")
            raise ValueError("Authentication failed with OpenRouter API. Please check your API key.")
        
        elif response.status_code == 503:
            logger.error("OpenRouter API service unavailable (503)")
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

def get_openrouter_model_status():
    """
    Check if the OpenRouter API and model are available
    Returns a dictionary with status information
    """
    try:
        # Simple API health check
        headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
        response = requests.get(
            "https://openrouter.ai/api/v1/auth/key",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "status": "available",
                "message": "OpenRouter API and Mistral-7B model are available",
                "using_fallback": False
            }
        else:
            return {
                "status": "error",
                "message": f"OpenRouter API returned status code {response.status_code}: {response.text}",
                "using_fallback": True
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking OpenRouter API status: {str(e)}",
            "using_fallback": True
        }
