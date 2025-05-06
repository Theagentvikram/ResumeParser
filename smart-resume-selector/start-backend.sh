#!/bin/bash
# Start the Smart Resume Selector backend

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

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "Ollama is not installed. Please install it from https://ollama.ai/"
    echo "You can continue without Ollama, but LLM summarization will use the fallback method."
else
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo "Starting Ollama..."
        ollama serve &
        # Wait for Ollama to start
        sleep 5
    fi
    
    # Check if Mistral model is available
    if ! ollama list | grep -q "mistral"; then
        echo "Pulling Mistral model..."
        ollama pull mistral:7b-instruct-v0.2
    fi
fi

# Start the backend server
echo "Starting backend server..."
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
