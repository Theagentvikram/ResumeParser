# Smart Resume Matcher

A lightweight, reliable resume matching system that uses regex-based extraction and semantic search to help recruiters find the best candidates.

## 🚀 Features

- **PDF Resume Upload**: Upload single or multiple resume PDFs
- **Regex-based Extraction**: Extract structured information from resumes
- **Semantic Search**: Match recruiter prompts to resumes using TF-IDF and cosine similarity
- **Filtering**: Filter by skills, job category, and years of experience
- **Clean UI**: Modern, responsive user interface

## 🛠️ Tech Stack

- **Frontend**: React with modern components
- **Backend**: FastAPI
- **PDF Parsing**: PyMuPDF
- **Text Analysis**: scikit-learn for TF-IDF vectorization and cosine similarity
- **Storage**: Simple JSON-based storage (no database setup required)

## 📋 How It Works

1. **Resume Upload**: Upload PDF resumes through the drag-and-drop interface
2. **Automatic Extraction**: The system extracts key information using regex patterns:
   - Name, email, phone
   - Skills
   - Education
   - Experience
   - Job role
3. **Semantic Search**: Enter a recruiter prompt to find matching candidates
   - Uses TF-IDF vectorization for text representation
   - Calculates cosine similarity between query and resumes
   - Returns top 5 matches with similarity scores
4. **Filtering**: Narrow down results by:
   - Required skills
   - Job category
   - Years of experience

## 🚀 Getting Started

### Prerequisites

1. Python 3.8+ with pip
2. Node.js 14+ with npm

### Installation & Setup

1. Clone the repository or navigate to the project directory:
   ```bash
   cd /Users/abhi/Documents/Projects/ResuMatch/resume-matcher
   ```

2. Make the start scripts executable:
   ```bash
   chmod +x start-backend.sh start-frontend.sh
   ```

3. Start the backend server:
   ```bash
   ./start-backend.sh
   ```
   This will:
   - Create a Python virtual environment
   - Install backend dependencies
   - Start the FastAPI server on port 8000

4. In a new terminal, start the frontend:
   ```bash
   ./start-frontend.sh
   ```
   This will:
   - Install frontend dependencies
   - Start the React development server on port 3000

5. Open your browser and navigate to:
   ```
   http://localhost:3000
   ```

## 📁 Project Structure

```
resume-matcher/
├── backend/                # FastAPI backend
│   ├── app.py              # Main backend application
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── utils/          # Utility functions
│   │   ├── styles/         # CSS styles
│   │   ├── App.js          # Main App component
│   │   └── index.js        # Entry point
│   └── package.json        # Node.js dependencies
├── data/                   # Data storage
│   ├── uploads/            # Uploaded resume files
│   ├── summaries/          # Generated summaries
│   └── db/                 # JSON database files
├── start-backend.sh        # Script to start backend
├── start-frontend.sh       # Script to start frontend
└── README.md               # Project documentation
```

## 💡 Usage Tips

1. **For best results**, upload PDF resumes with clear, standard formatting
2. **When searching**, be specific about skills, experience level, and job requirements
3. **Use filters** to narrow down results when you have many resumes
4. **View detailed information** by clicking the "View" button on each resume card
5. **Download original resumes** by clicking the "Download" button

## 🔧 Customization

- Add more skills to the extraction patterns in `backend/app.py`
- Modify the categories list in `frontend/src/components/FilterPanel.js`
- Adjust the styling in `frontend/src/styles/App.css`

## 📝 Notes

- This implementation uses simple JSON files for storage, making it easy to set up without database configuration
- All processing happens locally on your machine
- For production use, consider implementing a proper database and authentication
