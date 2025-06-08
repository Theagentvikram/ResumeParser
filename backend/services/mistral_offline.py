import os
import json
import re
import torch
from typing import Dict, List, Any, Optional
import logging
import time
from huggingface_hub import hf_hub_download
from transformers import AutoModelForCausalLM, AutoTokenizer
from services.claude_service import analyze_resume_with_regex

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if GPU is available
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Using device: {DEVICE} for LLM")

# Global variables for model and tokenizer
model = None
tokenizer = None

# Use a publicly available model that doesn't require login
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # Small model that works on CPU
LOCAL_MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models", "tinyllama")

def download_model_files():
    """Download model files if they don't exist locally"""
    try:
        # Create directory structure if it doesn't exist
        os.makedirs(LOCAL_MODEL_PATH, exist_ok=True)
        
        # Files to download
        files_to_download = [
            "config.json",
            "generation_config.json",
            "model-00001-of-00002.safetensors",
            "model-00002-of-00002.safetensors",
            "model.safetensors.index.json",
            "tokenizer.json",
            "tokenizer.model",
            "tokenizer_config.json",
            "special_tokens_map.json"
        ]
        
        logger.info(f"Checking for model files in {LOCAL_MODEL_PATH}")
        for filename in files_to_download:
            local_file_path = os.path.join(LOCAL_MODEL_PATH, filename)
            if not os.path.exists(local_file_path):
                logger.info(f"Downloading {filename} from Hugging Face Hub")
                hf_hub_download(
                    repo_id=MODEL_ID,
                    filename=filename,
                    local_dir=LOCAL_MODEL_PATH,
                    local_dir_use_symlinks=False
                )
                logger.info(f"Successfully downloaded {filename}")
                # Sleep briefly to avoid rate limiting
                time.sleep(0.5)
        
        return True
    except Exception as e:
        logger.error(f"Error downloading model files: {str(e)}")
        return False

def initialize_mistral_model(force_download=False):
    """Initialize the LLM model and tokenizer (load only once)"""
    global model, tokenizer
    
    try:
        # If model is already loaded, return immediately
        if model is not None and tokenizer is not None and not force_download:
            logger.info("Model already loaded in memory, reusing")
            return True
        
        logger.info("Starting LLM model initialization")
        
        # Download model files if needed or forced
        if force_download or not os.path.exists(os.path.join(LOCAL_MODEL_PATH, "tokenizer_config.json")):
            download_success = download_model_files()
            if not download_success:
                logger.error("Failed to download model files")
                return False
        
        # Load the tokenizer
        logger.info("Loading tokenizer")
        tokenizer = AutoTokenizer.from_pretrained(
            LOCAL_MODEL_PATH,
            local_files_only=True
        )
        
        # Load the model
        logger.info("Loading model with float32 precision (for CPU compatibility)")
        model = AutoModelForCausalLM.from_pretrained(
            LOCAL_MODEL_PATH,
            torch_dtype=torch.float32,  # Use float32 for CPU compatibility
            local_files_only=True,
            low_cpu_mem_usage=True
        )
        
        # Move model to appropriate device
        model.to(DEVICE)
        
        logger.info(f"Model loaded successfully on {DEVICE}")
        return True
    except Exception as e:
        logger.error(f"Error initializing model: {str(e)}")
        return False

def analyze_resume_with_mistral_offline(resume_text: str) -> Dict[str, Any]:
    """
    Analyze resume text using locally hosted LLM
    
    Args:
        resume_text: The text content of the resume
        
    Returns:
        Dictionary containing extracted information
    """
    logger.info("Starting offline LLM resume analysis")
    
    # Try to initialize the model if not already loaded
    if model is None or tokenizer is None:
        success = initialize_mistral_model()
        if not success:
            logger.warning("Failed to load LLM model, falling back to regex analysis")
            return analyze_resume_with_regex(resume_text)
    
    try:
        # Truncate text if needed - smaller models have limited context window
        max_chars = 4000  # Conservative limit
        if len(resume_text) > max_chars:
            logger.info(f"Truncating resume text from {len(resume_text)} to {max_chars} characters")
            resume_text = resume_text[:max_chars]
        
        # Prepare the prompt with a more reliable format for TinyLlama
        prompt = f"""<|system|>
You are an expert resume analyzer. You extract key information from resumes accurately.
<|user|>
Below is the text extracted from a resume. Please analyze it and extract the following information:

1. summary: A professional summary (3-4 sentences)
2. skills: A list of technical and soft skills found in the resume
3. experience: The total years of professional experience (as a number)
4. educationLevel: The highest education level (High School, Associate's, Bachelor's, Master's, PhD)
5. category: The job category that best fits this resume (e.g., Software Engineering, Data Science, Marketing)

Resume text:
```
{resume_text}
```

Format your response as a JSON object with the keys: "summary", "skills" (as an array), "experience" (as a number), "educationLevel", and "category". Only respond with the JSON.
<|assistant|>
"""
        
        logger.info("Generating response with TinyLlama model")
        
        # Create prompt inputs
        inputs = tokenizer(prompt, return_tensors="pt")
        if DEVICE == "cuda":
            inputs = inputs.to("cuda")
        
        # Generate the response - limiting tokens to reduce memory usage
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=600,
                temperature=0.1,
                top_p=0.95,
                do_sample=True
            )
        
        # Decode the output and extract text
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract the assistant's response (after the prompt)
        assistant_response = generated_text.split("<|assistant|>")[-1].strip()
        logger.info(f"Generated response length: {len(assistant_response)} chars")
        
        # Extract JSON from the text
        try:
            # Try to find a JSON object in the response
            json_match = re.search(r'(\{.*\})', assistant_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                result_dict = json.loads(json_str)
                
                # Validate and ensure all required fields are present
                analysis_result = {
                    "summary": result_dict.get("summary", "Professional with relevant skills and experience."),
                    "skills": result_dict.get("skills", ["Communication", "Problem Solving", "Teamwork"]),
                    "experience": int(result_dict.get("experience", 2)),
                    "educationLevel": result_dict.get("educationLevel", "Bachelor's"),
                    "category": result_dict.get("category", "Professional")
                }
                
                # Ensure skills is a list
                if not isinstance(analysis_result["skills"], list):
                    if isinstance(analysis_result["skills"], str):
                        # Split by commas if it's a string
                        analysis_result["skills"] = [skill.strip() for skill in analysis_result["skills"].split(",")]
                    else:
                        analysis_result["skills"] = []
                
                logger.info(f"Successfully extracted {len(analysis_result['skills'])} skills with LLM model")
                return analysis_result
            else:
                logger.error(f"No JSON found in model response")
                logger.debug(f"Raw response: {assistant_response[:200]}...")
                raise ValueError("No JSON data found in model response")
                
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Error parsing LLM response as JSON: {str(e)}")
            logger.debug(f"Raw response: {assistant_response[:200]}...")
            raise ValueError(f"Failed to parse model response as JSON: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error using offline LLM model: {str(e)}")
        return analyze_resume_with_regex(resume_text)

def preload_model():
    """Preload the model at startup"""
    logger.info("Preloading TinyLlama model")
    initialize_mistral_model()

def is_mistral_model_available():
    """Check if the LLM model can be loaded locally"""
    try:
        # Check if the model files exist locally
        if os.path.exists(LOCAL_MODEL_PATH) and os.path.exists(os.path.join(LOCAL_MODEL_PATH, "tokenizer_config.json")):
            logger.info("LLM model files found locally")
            return True
        
        # If we have internet, we can download the model
        logger.info("LLM model not found locally, but can be downloaded")
        return True
        
    except Exception as e:
        logger.error(f"Error checking LLM model availability: {str(e)}")
        return False 