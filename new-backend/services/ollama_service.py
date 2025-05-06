"""
Ollama service for interacting with the Mistral-7B-Instruct model
"""
import ollama
import json
import logging
import os
import re
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model name
MODEL_NAME = "mistral"

def ensure_model_available():
    """
    Ensure the Mistral model is available in Ollama
    
    Returns:
        bool: True if model is available, False otherwise
    """
    try:
        # List available models
        models = ollama.list()
        
        # Check if Mistral model is available
        for model in models.get('models', []):
            if model.get('name') == MODEL_NAME:
                logger.info(f"Model {MODEL_NAME} is available")
                return True
        
        # If model is not available, pull it
        logger.info(f"Model {MODEL_NAME} not found, pulling from Ollama library...")
        ollama.pull(MODEL_NAME)
        logger.info(f"Successfully pulled {MODEL_NAME}")
        return True
    except Exception as e:
        logger.error(f"Error ensuring model availability: {str(e)}")
        return False

def analyze_resume(resume_text: str) -> Dict[str, Any]:
    """
    Analyze a resume using the Mistral-7B-Instruct model via Ollama
    
    Args:
        resume_text: The text content of the resume
        
    Returns:
        Dictionary containing extracted information
    """
    logger.info("Starting resume analysis with Mistral-7B-Instruct")
    
    # Ensure model is available
    if not ensure_model_available():
        raise Exception("Failed to ensure model availability")
    
    # Truncate text if it's too long (to fit in context window)
    max_chars = 6000
    if len(resume_text) > max_chars:
        logger.info(f"Truncating resume text from {len(resume_text)} to {max_chars} characters")
        resume_text = resume_text[:max_chars]
    
    # Create a prompt for Mistral-7B-Instruct
    prompt = f"""Analyze this resume and extract key information as JSON:

```
{resume_text}
```

Extract the following information:
1. name: The full name of the person
2. skills: List of technical and soft skills
3. experience_years: Estimated years of experience as a number
4. education_level: Highest education level (e.g., "Bachelor's", "Master's", "PhD")
5. role: The primary job role or title
6. summary: A brief 1-2 sentence professional summary

Format your response as a valid JSON object with these fields.
"""
    
    try:
        # Generate response with Ollama
        logger.info("Generating response with Ollama")
        response = ollama.generate(
            model=MODEL_NAME,
            prompt=prompt,
            options={
                "temperature": 0.1,
                "top_p": 0.95,
                "num_predict": 1024
            }
        )
        
        # Extract generated text
        generated_text = response.get('response', '')
        logger.info(f"Generated response length: {len(generated_text)} chars")
        
        # Extract JSON from the response
        json_match = re.search(r'```json\s*(.*?)\s*```', generated_text, re.DOTALL)
        if json_match:
            json_text = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'(\{.*\})', generated_text, re.DOTALL)
            if json_match:
                json_text = json_match.group(1)
            else:
                json_text = generated_text
        
        # Clean up the text
        json_text = json_text.strip()
        
        # Parse the JSON
        try:
            result = json.loads(json_text)
            
            # Validate and provide defaults for missing fields
            analysis_result = {
                "name": result.get("name", "Unknown"),
                "summary": result.get("summary", "Professional with relevant skills and experience."),
                "skills": result.get("skills", []),
                "experience_years": float(result.get("experience_years", 0)),
                "education_level": result.get("education_level", "Unknown"),
                "role": result.get("role", "Professional")
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
            
            # Try to extract partial data
            name_match = re.search(r'"name":\s*"([^"]+)"', generated_text)
            name = name_match.group(1) if name_match else "Unknown"
            
            skills_match = re.search(r'"skills":\s*\[(.*?)\]', generated_text, re.DOTALL)
            skills_text = skills_match.group(1) if skills_match else ""
            skills = [s.strip().strip('"\'') for s in skills_text.split(",")]
            
            # Return partial data
            return {
                "name": name,
                "summary": "Could not fully parse the resume.",
                "skills": skills,
                "experience_years": 0,
                "education_level": "Unknown",
                "role": "Professional"
            }
            
    except Exception as e:
        logger.error(f"Error in resume analysis: {str(e)}")
        raise Exception(f"Resume analysis failed: {str(e)}")

def generate_embedding(text: str) -> List[float]:
    """
    Generate an embedding for a text using the Mistral model
    
    Args:
        text: The text to embed
        
    Returns:
        List of floats representing the embedding
    """
    try:
        # Ensure model is available
        if not ensure_model_available():
            raise Exception("Failed to ensure model availability")
        
        # Generate embedding with Ollama
        response = ollama.embeddings(
            model=MODEL_NAME,
            prompt=text
        )
        
        # Return the embedding
        return response.get('embedding', [])
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        raise Exception(f"Failed to generate embedding: {str(e)}")

def search_resumes_by_prompt(prompt: str, resumes_embeddings: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
    """
    Search for resumes based on a natural language prompt
    
    Args:
        prompt: The search prompt
        resumes_embeddings: List of resume dictionaries with embeddings
        top_n: Number of top results to return
        
    Returns:
        List of top matching resumes with scores
    """
    try:
        # Generate embedding for the prompt
        prompt_embedding = generate_embedding(prompt)
        
        # Calculate similarity scores
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        # Prepare embeddings for comparison
        prompt_embedding_array = np.array(prompt_embedding).reshape(1, -1)
        
        results = []
        for resume in resumes_embeddings:
            if 'embedding' in resume and resume['embedding'] is not None:
                resume_embedding = np.array(resume['embedding']).reshape(1, -1)
                similarity = float(cosine_similarity(prompt_embedding_array, resume_embedding)[0][0])
                
                # Add to results
                results.append({
                    'resume': resume,
                    'score': similarity
                })
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N results
        return results[:top_n]
    except Exception as e:
        logger.error(f"Error searching resumes: {str(e)}")
        raise Exception(f"Failed to search resumes: {str(e)}")
