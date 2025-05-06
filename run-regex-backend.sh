#!/bin/bash

# ResuMatch Regex-Based Backend Startup Script
echo "🚀 Starting ResuMatch Regex-Based Backend 🚀"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "🔄 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install required packages if not already installed
if ! pip show fastapi > /dev/null; then
    echo "🔄 Installing required packages..."
    pip install fastapi uvicorn python-multipart pymupdf numpy pydantic
fi

# Start the backend
echo "🚀 Starting the backend..."
python3 regex-backend.py
