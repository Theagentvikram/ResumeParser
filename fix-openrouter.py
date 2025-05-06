#!/usr/bin/env python3
"""
Fix script for OpenRouter API integration
This script will update the OpenRouter API key in all necessary files
"""
import os
import json
import re
from pathlib import Path

# The correct API key from the user
CORRECT_API_KEY = "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"
MODEL = "mistralai/mistral-7b-instruct:free"

# Files to update
files_to_update = [
    ".env",
    "backend/services/openrouter_service.py",
    "test-openrouter-direct.py",
    "test-openrouter-simple.py"
]

# Update the API key in all files
def update_api_key():
    """Update the OpenRouter API key in all necessary files"""
    print("Updating OpenRouter API key in all necessary files...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    for file_path in files_to_update:
        full_path = os.path.join(base_dir, file_path)
        
        if not os.path.exists(full_path):
            print(f"File not found: {full_path}")
            continue
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Replace any existing OpenRouter API key with the correct one
        new_content = re.sub(
            r'(OPENROUTER_API_KEY\s*=\s*["\'])sk-or-v1-[a-f0-9]+(["\'])', 
            f'\\1{CORRECT_API_KEY}\\2', 
            content
        )
        
        # Also try another pattern for Python variables
        new_content = re.sub(
            r'(API_KEY\s*=\s*["\'])sk-or-v1-[a-f0-9]+(["\'])', 
            f'\\1{CORRECT_API_KEY}\\2', 
            new_content
        )
        
        if new_content != content:
            with open(full_path, 'w') as f:
                f.write(new_content)
            print(f"Updated API key in {file_path}")
        else:
            print(f"No API key found or already correct in {file_path}")

# Create a .env file if it doesn't exist
def ensure_env_file():
    """Create or update the .env file with the correct OpenRouter API key"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Check if OpenRouter API key is already in the .env file
        if "OPENROUTER_API_KEY" in content:
            # Update the existing key
            new_content = re.sub(
                r'OPENROUTER_API_KEY=sk-or-v1-[a-f0-9]+', 
                f'OPENROUTER_API_KEY={CORRECT_API_KEY}', 
                content
            )
            
            if "OPENROUTER_MODEL" not in content:
                new_content += f"\nOPENROUTER_MODEL={MODEL}\n"
        else:
            # Add the OpenRouter API key and model
            new_content = content.rstrip() + f"\n\n# OpenRouter API Configuration\nOPENROUTER_API_KEY={CORRECT_API_KEY}\nOPENROUTER_MODEL={MODEL}\n"
    else:
        # Create a new .env file
        new_content = f"# ResuMatch Environment Configuration\n\n# OpenRouter API Configuration\nOPENROUTER_API_KEY={CORRECT_API_KEY}\nOPENROUTER_MODEL={MODEL}\n"
    
    with open(env_path, 'w') as f:
        f.write(new_content)
    
    print(f"Updated .env file with OpenRouter API key and model")

# Set ANALYZER_MODE to use the API
def set_analyzer_mode():
    """Set ANALYZER_MODE to 'api' in the .env file"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
        
        # Check if ANALYZER_MODE is already in the .env file
        if "ANALYZER_MODE" in content:
            # Update the existing mode
            new_content = re.sub(
                r'ANALYZER_MODE=\w+', 
                'ANALYZER_MODE=api', 
                content
            )
        else:
            # Add the ANALYZER_MODE
            new_content = content.rstrip() + "\nANALYZER_MODE=api\n"
        
        with open(env_path, 'w') as f:
            f.write(new_content)
        
        print("Set ANALYZER_MODE to 'api' in .env file")

if __name__ == "__main__":
    print("🔧 OpenRouter API Fix Script 🔧")
    print("===============================")
    
    # Update the API key in all files
    update_api_key()
    
    # Ensure the .env file exists and has the correct API key
    ensure_env_file()
    
    # Set ANALYZER_MODE to use the API
    set_analyzer_mode()
    
    print("\n✅ OpenRouter API configuration has been fixed!")
    print("Please restart your backend server for the changes to take effect.")
    print("You can do this by running: ./start-backend.sh")
