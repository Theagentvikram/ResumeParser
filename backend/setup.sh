#!/bin/bash

# Exit on error
set -e

# Create and activate virtual environment
echo "Creating virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip and setuptools
echo "Upgrading pip and setuptools..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating storage directories..."
mkdir -p storage/resumes

# Set environment variables
echo "Setting up environment variables..."
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env <<EOL
# API Settings
PORT=8000
HOST=0.0.0.0

# OpenRouter API
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Feature Flags
ENABLE_CORS=true
DEBUG_MODE=true
EOL
    echo "Please update the .env file with your actual API keys and settings."
else
    echo ".env file already exists. Make sure it contains all required variables."
fi

echo "Setup complete! Activate the virtual environment with 'source venv/bin/activate'"
