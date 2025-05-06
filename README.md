# ResuMatch

A recruiter-facing Resume Selection App that uses AI to analyze and match resumes based on queries.

## Features

- Upload student resumes in PDF format
- AI-powered resume summarization and analysis
- Semantic search with embeddings
- Beautiful and modern React UI
- Fully cloud-based - no local models or embeddings

## Technology Stack

### Frontend
- React with TypeScript
- Tailwind CSS and shadcn/ui
- Framer Motion for animations
- React Router for navigation
- Axios for API communication

### Backend
- FastAPI (Python)
- Hugging Face Inference APIs for AI capabilities
- SQLite for local data storage
- PDF processing with PyMuPDF and pdfplumber
- Vector search with cosine similarity

### Storage Options
- Local file storage (default for development)
- Supabase Storage (optional for production)

## Setup Instructions

### Prerequisites
- Node.js 16+ and npm
- Python 3.9+
- Git

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Copy the example environment file and configure:
   ```bash
   cp .env.example .env
   ```
   Edit the `.env` file and set your Hugging Face API key (optional)

6. Start the backend server:
   ```bash
   python main.py
   ```
   The backend will be available at http://localhost:8000

### Frontend Setup
1. Install dependencies:
   ```bash
   npm install
   ```

2. Copy the example environment file and configure:
   ```bash
   cp .env.example .env
   ```
   Make sure `VITE_API_URL` points to your backend server

3. Start the development server:
   ```bash
   npm run dev
   ```
   The frontend will be available at http://localhost:5173

### Quick Start
You can also use the provided script to start the backend:
```bash
chmod +x start-backend.sh
./start-backend.sh
```

## Usage

### Recruiter Login
- Username: `recruiter`
- Password: `password123`

### Applicant Login (for testing)
- Username: `user`
- Password: `password123`

## Deployment

### Frontend
- Deploy to Vercel, Netlify, or GitHub Pages

### Backend
- Deploy to Render, Replit, or any other free-tier service that supports Python

## License
MIT
