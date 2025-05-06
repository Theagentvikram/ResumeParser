#!/bin/bash
# Start the Resume Matcher backend

# Set up virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r backend/requirements.txt

# Start the backend server
echo "Starting backend server..."
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
