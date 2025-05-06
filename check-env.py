#!/usr/bin/env python3
"""
Check environment variables for OpenRouter API
"""
import os
from dotenv import load_dotenv

# Load environment variables with force reload
print("Loading environment variables with force reload...")
load_dotenv(override=True)

# Print all environment variables for debugging
print("\nAll environment variables:")
for key, value in os.environ.items():
    if key.startswith("OPENROUTER"):
        print(f"  {key}: {value}")
        
# Read directly from .env file
print("\nReading directly from .env file:")
try:
    with open(".env", "r") as f:
        for line in f:
            if line.strip() and not line.strip().startswith("#") and "=" in line:
                key, value = line.strip().split("=", 1)
                if key.startswith("OPENROUTER"):
                    print(f"  {key}={value}")
except Exception as e:
    print(f"Error reading .env file: {e}")

# Get API key from environment
api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL")

print(f"OPENROUTER_API_KEY: {api_key[:10]}...{api_key[-5:] if api_key else 'None'}")
print(f"OPENROUTER_MODEL: {model}")

# Check if the API key is in the correct format
if api_key and api_key.startswith("sk-or-v1-"):
    print("✅ API key format appears correct (starts with sk-or-v1-)")
else:
    print("❌ API key format appears incorrect (should start with sk-or-v1-)")

# Check if the model is in the correct format
if model and model == "mistralai/mistral-7b-instruct:free":
    print("✅ Model format appears correct")
else:
    print("❌ Model format appears incorrect (should be mistralai/mistral-7b-instruct:free)")
