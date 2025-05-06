"""
Main FastAPI application for ResuMatch
"""
import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from routes.resume_routes import router as resume_router
from database.models import init_db

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ResuMatch API",
    description="API for ResuMatch Resume Selection Platform",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development. In production, specify domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(resume_router)

# Create upload directory if it doesn't exist
os.makedirs(os.path.join(os.path.dirname(__file__), "uploads", "resumes"), exist_ok=True)

# Mount static files
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
async def root():
    """
    Root endpoint for health check
    """
    return {
        "status": "ok",
        "message": "ResuMatch API v2 is running",
        "docs_url": "/docs"
    }

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "ok",
        "version": "2.0.0"
    }

@app.on_event("startup")
async def startup_event():
    """
    Initialize the database on startup
    """
    try:
        # Initialize the database
        init_db()
        logger.info("Database initialized successfully")
        
        # Check if Ollama is available
        try:
            from services.ollama_service import ensure_model_available
            if ensure_model_available():
                logger.info("Ollama model is available")
            else:
                logger.warning("Ollama model is not available. Please install Ollama and pull the mistral:7b-instruct-v0.2 model.")
        except Exception as e:
            logger.warning(f"Failed to check Ollama model: {str(e)}")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
