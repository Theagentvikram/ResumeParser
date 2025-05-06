#!/bin/bash

# Script to clean up and set up Mistral 7B Instruct model for ResuMatch

echo "🧹 ResuMatch Model Cleanup and Setup Script 🧹"
echo "=============================================="

# Create models directory if it doesn't exist
mkdir -p backend/models

# Clean up existing models
echo "🗑️ Cleaning up existing models..."
rm -f backend/models/llama-2-7b-chat.Q4_K_M.gguf
rm -f backend/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
rm -rf backend/models/tinyllama
rm -f backend/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf

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
    # Reinstall to ensure clean installation
    echo "🔄 Reinstalling llama-cpp-python..."
    pip uninstall -y llama-cpp-python
    pip install llama-cpp-python==0.2.19
else
    echo "📦 Installing llama-cpp-python..."
    pip install llama-cpp-python==0.2.19
fi

# Download Mistral 7B Instruct model
MISTRAL_MODEL_PATH="backend/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
echo "📥 Downloading Mistral 7B Instruct model..."

# Use wget with progress and resume capability
if command -v wget > /dev/null; then
    wget -c https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf -O "$MISTRAL_MODEL_PATH"
else
    # Fallback to curl if wget is not available
    curl -L --retry 5 --retry-delay 5 -C - https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF/resolve/main/mistral-7b-instruct-v0.2.Q4_K_M.gguf -o "$MISTRAL_MODEL_PATH"
fi

# Verify the download
if [ -f "$MISTRAL_MODEL_PATH" ]; then
    MODEL_SIZE=$(du -h "$MISTRAL_MODEL_PATH" | cut -f1)
    echo "✅ Mistral model downloaded successfully to: $MISTRAL_MODEL_PATH"
    echo "   File size: $MODEL_SIZE"
    
    # Expected file size is approximately 4GB
    SIZE_BYTES=$(stat -f%z "$MISTRAL_MODEL_PATH")
    if [ "$SIZE_BYTES" -lt 3000000000 ]; then
        echo "⚠️ Warning: Model file size ($SIZE_BYTES bytes) is smaller than expected."
        echo "   The download may have been interrupted. Consider running this script again."
    fi
else
    echo "❌ Failed to download Mistral model"
    exit 1
fi

# Update the environment variable to use llama_cpp
echo "🔄 Setting ANALYZER_MODE to llama_cpp in .env file..."
if [ -f "backend/.env" ]; then
    if grep -q "ANALYZER_MODE" backend/.env; then
        sed -i '' 's/ANALYZER_MODE=.*/ANALYZER_MODE="llama_cpp"/' backend/.env
    else
        echo 'ANALYZER_MODE="llama_cpp"' >> backend/.env
    fi
else
    echo 'ANALYZER_MODE="llama_cpp"' > backend/.env
fi

echo "✅ Setup completed. Try starting the backend with ./start-backend.sh"
