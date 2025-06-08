# ResuMatch Backend

A FastAPI-based backend for the ResuMatch Resume Selection App. This backend provides the following features:

- Resume PDF text extraction
- Resume analysis with LLM via Hugging Face APIs
- Vector embeddings for semantic search
- Resume storage and retrieval
- Resume search by similarity

## Technology Stack

- FastAPI: Modern, fast web framework for building APIs
- Hugging Face Inference APIs: For resume analysis and embeddings
- SQLite: Simple local database for resume storage
- Supabase (optional): For production-level storage
- PyMuPDF/pdfplumber: For PDF text extraction
- scikit-learn: For similarity calculations

## Setup Instructions

### Prerequisites

- Python 3.9+ 
- pip or poetry for package management

### Installation

1. Clone the repository
2. Navigate to the backend directory
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy the environment variables template:
   ```bash
   cp .env.example .env
   ```
5. Edit the `.env` file with your configuration values

### Configuration

The backend can be configured using environment variables:

- `HUGGINGFACE_API_KEY`: Your Hugging Face API key (for production)
- `SUPABASE_URL` and `SUPABASE_KEY`: Only needed if using Supabase for storage
- `PORT`: Port for the API server (default: 8000)
- `HOST`: Host for the API server (default: 0.0.0.0)
- `CORS_ORIGINS`: Allowed CORS origins

### Running the Backend

Start the development server:

```bash
cd backend
python main.py
```

This will start the server on http://localhost:8000.

### API Documentation

Once running, you can access the interactive API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

- `POST /resumes/analyze`: Analyze a resume PDF
- `POST /resumes/upload`: Upload a resume with metadata
- `POST /resumes/search`: Search for resumes by query and filters
- `GET /resumes`: Get all uploaded resumes
- `GET /download/{file_path}`: Download a resume file

## Production Deployment

For production deployment, consider the following:

1. Use a proper ASGI server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   
2. Set up a proper database:
   - SQLite is suitable for small deployments
   - Consider Supabase or another hosted database for larger deployments
   
3. Set proper CORS restrictions in production:
   - Edit the CORS_ORIGINS in your .env file
   
4. Deploy on a free-tier service:
   - Render.com (recommended)
   - Replit
   - Fly.io
   - Railway 