#!/bin/bash
# Start the Resume Matcher frontend

# Navigate to frontend directory
cd "$(dirname "$0")/frontend"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Start the development server
echo "Starting frontend development server..."
npm start
