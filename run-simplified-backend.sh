#!/bin/bash

# Script to run the simplified ResuMatch backend

echo "🚀 Starting Simplified ResuMatch Backend 🚀"
echo "=========================================="

# Create uploads directory if it doesn't exist
mkdir -p uploads/resumes

# Make sure we have the Mistral model
if [ ! -f "backend/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf" ]; then
    echo "⚠️ Mistral model not found, will use existing Llama model"
fi

# Activate the virtual environment
if [ -d "backend/venv" ]; then
    echo "🔄 Activating virtual environment..."
    source backend/venv/bin/activate
else
    echo "⚠️ Virtual environment not found, using system Python"
fi

# Run the backend
echo "🚀 Starting the backend..."
python3 simplified-backend.py
