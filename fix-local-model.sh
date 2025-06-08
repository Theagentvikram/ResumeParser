#!/bin/bash

# Script to fix the local model issues with ResuMatch

echo "🔧 ResuMatch Local Model Fix Script 🔧"
echo "======================================="

# Create virtual environment if it doesn't exist
if [ ! -d "backend/venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv backend/venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source backend/venv/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r backend/requirements.txt

# Check if llama-cpp-python is installed
if pip show llama-cpp-python > /dev/null; then
    echo "✅ llama-cpp-python is installed"
else
    echo "⚠️ llama-cpp-python is not installed. Installing now..."
    pip install llama-cpp-python==0.2.19
fi

# Check if model file exists
MODEL_PATH="backend/models/llama-2-7b-chat.Q4_K_M.gguf"
if [ -f "$MODEL_PATH" ]; then
    echo "✅ Model file found at: $MODEL_PATH"
    MODEL_SIZE=$(du -h "$MODEL_PATH" | cut -f1)
    echo "   File size: $MODEL_SIZE"
else
    echo "❌ Model file not found at: $MODEL_PATH"
    echo "   This could be why the local model is not working."
fi

# Update the environment variable to use llama_cpp
echo "🔄 Setting ANALYZER_MODE to llama_cpp in .env file..."
if grep -q "ANALYZER_MODE" backend/.env; then
    sed -i '' 's/ANALYZER_MODE=.*/ANALYZER_MODE="llama_cpp"/' backend/.env
else
    echo 'ANALYZER_MODE="llama_cpp"' >> backend/.env
fi

echo "✅ Fix script completed. Try starting the backend again with ./start-backend.sh"
