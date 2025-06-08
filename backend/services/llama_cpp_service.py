import os
import json
import re
import logging
from typing import Dict, List, Any, Optional
from services.claude_service import analyze_resume_with_regex

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import llama_cpp (lazy import to avoid startup errors if not being used)
try:
    import llama_cpp
    LLAMA_CPP_AVAILABLE = True
    logger.info("llama_cpp is available for local LLM inference")
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    logger.warning("llama_cpp is not available. Local LLM inference will not work.")

# Model settings
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
DEFAULT_MODEL_PATH = os.path.join(MODELS_DIR, "mistral-7b-instruct-v0.2.Q4_K_M.gguf")

# Alternative model URL for a smaller, faster model (keeping as fallback)
TINY_LLAMA_URL = "https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

# Global variable to hold the model
llm = None

def initialize_llm(model_path=None, n_ctx=4096, n_gpu_layers=0):
    """Initialize the LLM using llama.cpp"""
    global llm
    
    if not LLAMA_CPP_AVAILABLE:
        logger.error("Cannot initialize LLM: llama_cpp module not available")
        return False

    try:
        if llm is not None:
            logger.info("LLM already loaded, reusing existing instance")
            return True
            
        # Use provided model path or default
        model_path = model_path or DEFAULT_MODEL_PATH
        
        # Check if model file exists
        if not os.path.exists(model_path):
            logger.error(f"Model file not found: {model_path}")
            
            # Try to download TinyLlama as a fallback
            tiny_llama_path = os.path.join(MODELS_DIR, "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
            if not os.path.exists(tiny_llama_path):
                logger.info(f"Downloading TinyLlama model from {TINY_LLAMA_URL}...")
                tiny_llama_path = download_model(TINY_LLAMA_URL)
                if not tiny_llama_path:
                    return False
            
            model_path = tiny_llama_path
            logger.info(f"Using TinyLlama model instead: {model_path}")
            
        logger.info(f"Loading model from {model_path}...")
        
        # Create the Llama model with optimized settings
        llm = llama_cpp.Llama(
            model_path=model_path,
            n_ctx=n_ctx,           # Increased context size for Mistral
            n_gpu_layers=n_gpu_layers,  # Number of layers to offload to GPU
            verbose=False,         # No verbose output
            n_threads=4,           # Use multiple threads for faster inference
            n_batch=512            # Batch size for faster inference
        )
        
        logger.info(f"Model loaded successfully: {model_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing LLM: {str(e)}")
        return False

def analyze_resume_with_llama_cpp(resume_text: str) -> Dict[str, Any]:
    """
    Analyze a resume using a local LLM via llama.cpp
    
    Args:
        resume_text: The text content of the resume
        
    Returns:
        Dictionary containing extracted information
    """
    logger.info("Starting local LLM resume analysis with llama.cpp")
    
    # Check if llama_cpp is available
    if not LLAMA_CPP_AVAILABLE:
        logger.warning("llama_cpp is not available, falling back to regex analysis")
        return analyze_resume_with_regex(resume_text)
    
    # Try to use TinyLlama first (faster)
    tiny_llama_path = os.path.join(MODELS_DIR, "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
    if os.path.exists(tiny_llama_path):
        logger.info("Using TinyLlama model for faster analysis")
        if not initialize_llm(model_path=tiny_llama_path, n_ctx=1024):  # Even smaller context for TinyLlama
            logger.warning("Failed to initialize TinyLlama, falling back to regex analysis")
            return analyze_resume_with_regex(resume_text)
    else:
        # Initialize the default model if TinyLlama is not available
        if not initialize_llm(n_ctx=4096):  # Increased context size for Mistral
            logger.warning("Failed to initialize LLM, falling back to regex analysis")
            return analyze_resume_with_regex(resume_text)
    
    try:
        # Truncate text to fit in context window (conservative limit)
        max_chars = 2000  # Increased from 1000 to 2000 for Mistral's larger context
        if len(resume_text) > max_chars:
            logger.info(f"Truncating resume text from {len(resume_text)} to {max_chars} characters")
            resume_text = resume_text[:max_chars]
        
        # Create a prompt for Mistral 7B Instruct
        prompt = f"""<s>[INST]Analyze this resume and extract key information as JSON:

```
{resume_text}
```

Extract: summary (1-2 sentences), skills (list), experience (years as number), educationLevel (highest degree), category (job field).[/INST]

```json
"""
        
        logger.info("Generating response with local LLM")
        
        # Generate completion with optimized settings
        response = llm(
            prompt,
            max_tokens=256,  # Reduced from 512 to 256
            temperature=0.1,
            top_p=0.95,
            stop=["</s>", "[/INST]"]
        )
        
        # Extract generated text
        generated_text = response["choices"][0]["text"] if "choices" in response else ""
        
        # Try to complete the JSON object if it was cut off
        if generated_text and not "}" in generated_text:
            generated_text += '}'
            
        # Make sure it starts with a proper JSON format
        if generated_text and not generated_text.startswith('{'):
            generated_text = '{' + generated_text
        
        logger.info(f"Generated response length: {len(generated_text)} chars")
        
        # Extract and parse the JSON
        try:
            # Clean the text to ensure it's valid JSON
            json_text = generated_text.strip()
            
            # Add closing bracket if missing
            bracket_diff = json_text.count('{') - json_text.count('}')
            if bracket_diff > 0:
                json_text += '}' * bracket_diff
                
            # Parse the JSON
            result_dict = json.loads(json_text)
            
            # Create a standardized result with default values for missing fields
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
            
            logger.info(f"Successfully extracted {len(analysis_result['skills'])} skills with local LLM")
            return analysis_result
            
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing LLM response as JSON: {str(e)}")
            logger.debug(f"Raw response: {generated_text[:200]}...")
            
            # Try to extract partial data if possible
            try:
                # Look for skill lists in brackets
                skills_match = re.search(r'"skills":\s*\[(.*?)\]', generated_text)
                skills = []
                if skills_match:
                    skills_text = skills_match.group(1)
                    skills = [s.strip().strip('"\'') for s in skills_text.split(",")]
                
                # Look for summary
                summary_match = re.search(r'"summary":\s*"(.*?)"', generated_text)
                summary = "Professional with relevant experience."
                if summary_match:
                    summary = summary_match.group(1)
                
                # Experience years
                exp_match = re.search(r'"experience":\s*(\d+)', generated_text)
                experience = 2
                if exp_match:
                    experience = int(exp_match.group(1))
                
                # Education level
                edu_match = re.search(r'"educationLevel":\s*"(.*?)"', generated_text)
                education = "Bachelor's"
                if edu_match:
                    education = edu_match.group(1)
                
                # Job category
                cat_match = re.search(r'"category":\s*"(.*?)"', generated_text)
                category = "Professional"
                if cat_match:
                    category = cat_match.group(1)
                
                # Return extracted data
                return {
                    "summary": summary,
                    "skills": skills if skills else ["Communication", "Problem Solving"],
                    "experience": experience,
                    "educationLevel": education,
                    "category": category
                }
            except Exception:
                # If all extraction fails, fall back to regex
                logger.warning("Could not extract partial data, falling back to regex analysis")
                return analyze_resume_with_regex(resume_text)
    
    except Exception as e:
        logger.error(f"Error using local LLM: {str(e)}")
        return analyze_resume_with_regex(resume_text)

def download_model(model_url=None):
    """
    Download a model if not present locally.
    Similar to how LMStudio would download models.
    """
    import requests
    from tqdm import tqdm
    
    # Default to a small GGUF model if none specified
    model_url = model_url or "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"
    model_name = os.path.basename(model_url)
    model_path = os.path.join(MODELS_DIR, model_name)
    
    # Create models directory if it doesn't exist
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    # Check if model already exists
    if os.path.exists(model_path):
        logger.info(f"Model already exists at {model_path}")
        return model_path
    
    try:
        logger.info(f"Downloading model from {model_url}...")
        
        # Start download with progress bar
        response = requests.get(model_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(model_path, 'wb') as f, tqdm(
            desc=model_name,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
        ) as bar:
            for data in response.iter_content(chunk_size=1024*1024):
                size = f.write(data)
                bar.update(size)
        
        logger.info(f"Model downloaded successfully to {model_path}")
        return model_path
    
    except Exception as e:
        logger.error(f"Error downloading model: {str(e)}")
        return None

def is_llama_cpp_available():
    """Check if llama.cpp integration is available"""
    return LLAMA_CPP_AVAILABLE