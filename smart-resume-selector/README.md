# Smart Resume Selector

A powerful resume analysis and matching tool that uses regex-based PDF extraction, Mistral-7B-Instruct LLM summarization, and semantic search to help recruiters find the best candidates.

## 📋 Features

- **PDF Resume Upload**: Upload single or multiple resume PDFs
- **Regex-based Extraction**: Extract structured information from resumes using regex patterns
- **Mistral-7B-Instruct Summarization**: Generate concise summaries from extracted fields
- **Semantic Search**: Match recruiter prompts to resumes using cosine similarity
- **Filtering**: Filter by skills, job category, and years of experience
- **Local-only Processing**: All processing happens locally, no data sent to external APIs

## 🧠 How It Works

### 1. PDF Upload and Regex Extraction
- Extracts raw text using PyMuPDF
- Applies regex to extract fields like:
  - Name
  - Email
  - Phone
  - Skills
  - Education
  - Experience
  - Projects
- Stores structured data in SQLite

### 2. LLM Summarization (Mistral 7B - Instruct)
- Sends only the extracted fields to the LLM for summarizing
- Uses Ollama for local LLM inference
- Generates concise professional summaries and key skills

### 3. Embedding + Matching
- Creates sentence embeddings of LLM-generated summaries using SentenceTransformers
- Embeds recruiter prompts
- Uses cosine similarity to return Top 5 matching resumes

### 4. Recruiter Interface
- Text box to enter prompts
- Filters for skills, experience, job category
- Results table showing matched resumes with:
  - Summary
  - Matching Score
  - View/Download options

## 🛠️ Tech Stack

- **Frontend**: React / Next.js with TypeScript
- **Backend**: FastAPI
- **PDF Parsing**: PyMuPDF
- **Regex Extraction**: Python `re` module
- **LLM**: Mistral-7B via Ollama
- **Embeddings**: SentenceTransformers (`all-MiniLM-L6-v2`)
- **Similarity**: Cosine Similarity
- **Storage**: SQLite + FileSystem

## 🚀 Getting Started

### Prerequisites

1. Python 3.8+ with pip
2. Node.js 16+ with npm
3. [Ollama](https://ollama.ai/) for local LLM inference

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd smart-resume-selector
   ```

2. Install Ollama (if not already installed):
   ```bash
   # macOS
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # For other platforms, visit https://ollama.ai/
   ```

3. Make the start scripts executable:
   ```bash
   chmod +x start-backend.sh start-frontend.sh
   ```

### Running the Application

1. Start the backend:
   ```bash
   ./start-backend.sh
   ```
   This will:
   - Create a Python virtual environment
   - Install backend dependencies
   - Start Ollama if not running
   - Pull the Mistral model if needed
   - Start the FastAPI server on port 8000

2. In a new terminal, start the frontend:
   ```bash
   ./start-frontend.sh
   ```
   This will:
   - Install frontend dependencies
   - Start the Next.js development server on port 3000

3. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

## 📁 Project Structure

```
smart-resume-selector/
├── backend/                  # FastAPI backend
│   ├── services/             # Core services
│   │   ├── pdf_extractor.py  # Regex-based PDF extraction
│   │   ├── mistral_service.py # LLM integration
│   │   ├── embedding_service.py # Semantic search
│   │   └── database_service.py # SQLite storage
│   ├── main.py               # FastAPI application
│   └── requirements.txt      # Python dependencies
├── frontend/                 # Next.js frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Next.js pages
│   │   └── styles/           # CSS styles
│   ├── package.json          # Node.js dependencies
│   └── next.config.js        # Next.js configuration
├── uploads/                  # Uploaded resume files
├── summaries/                # Generated summaries
├── db/                       # SQLite database
├── start-backend.sh          # Script to start backend
├── start-frontend.sh         # Script to start frontend
└── README.md                 # Project documentation
```

## 📝 Usage

1. **Upload Resumes**:
   - Use the upload panel to add single or multiple PDF resumes
   - Resumes will be processed in the background

2. **Search for Candidates**:
   - Enter a detailed prompt describing your ideal candidate
   - Example: "Experienced Python developer with AWS skills and machine learning experience"

3. **Apply Filters** (optional):
   - Filter by specific skills
   - Filter by job category
   - Filter by years of experience

4. **View Results**:
   - See the top matching candidates
   - View match percentage
   - Expand entries to see full summaries and key skills
   - Download original resumes

## ⚠️ Limitations

- PDF extraction quality depends on the PDF structure
- Local LLM performance depends on your hardware
- Currently only supports PDF format

## 🔒 Privacy

All processing happens locally on your machine:
- No data is sent to external APIs
- Resumes are stored only in your local database
- The LLM runs locally via Ollama

## 📄 License

This project is open-source and available under the MIT License.
