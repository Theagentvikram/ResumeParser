#!/bin/bash

# Script to set up and start the new ResuMatch backend

echo "🚀 ResuMatch Backend Setup and Start Script 🚀"
echo "=============================================="

# Create virtual environment if it doesn't exist
if [ ! -d "new-backend/venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv new-backend/venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source new-backend/venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r new-backend/requirements.txt

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "⚠️ Ollama is not installed. Please install Ollama from https://ollama.ai"
    echo "After installing Ollama, run: ollama pull mistral:7b-instruct-v0.2"
else
    echo "✅ Ollama is installed"
    
    # Check if Mistral model is available
    if ollama list | grep -q "mistral:7b-instruct-v0.2"; then
        echo "✅ Mistral model is available"
    else
        echo "📥 Pulling Mistral model..."
        ollama pull mistral:7b-instruct-v0.2
    fi
fi

# Create necessary directories
mkdir -p new-backend/uploads/resumes
mkdir -p new-backend/database

# Start the backend
echo "🚀 Starting the backend..."
cd new-backend && python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
