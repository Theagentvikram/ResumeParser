#!/usr/bin/env python3
"""
Test script for checking the OpenRouter API key
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the API key from environment variables
API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

# Print the API key being used (first 10 chars and last 5 chars only for security)
print(f"Using API key: {API_KEY[:10]}...{API_KEY[-5:]}")
print(f"API key length: {len(API_KEY)} characters")

# OpenRouter API URL for checking models (doesn't require a full API call)
API_URL = "https://openrouter.ai/api/v1/models"

def test_openrouter_api_key():
    """Test the OpenRouter API key"""
    print(f"Testing OpenRouter API key with models endpoint: {API_URL}")
    
    # Set up the headers with authentication
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://resumatch.app",  # Replace with your actual domain
        "X-Title": "ResuMatch",  # Your app name
        "OpenAI-Organization": "org-",  # Required for OpenRouter
        "User-Agent": "ResuMatch/1.0"  # Helpful for debugging
    }
    
    try:
        # Make the API call
        print("Sending request to OpenRouter API...")
        response = requests.get(API_URL, headers=headers)
        
        # Print response status and headers for debugging
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
            result = response.json()
            print("\n✅ Success! API key is valid")
            
            # Print available models
            print("\n--- Available Models ---")
            models = result.get("data", [])
            for model in models:
                model_id = model.get("id", "Unknown")
                if "free" in model_id.lower():
                    print(f"- {model_id} (FREE)")
                else:
                    print(f"- {model_id}")
            
            return True
        elif response.status_code == 401:
            print("\n❌ Authentication failed (401): API key is invalid or expired")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"\n❌ API call failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 OpenRouter API Key Test 🔍")
    print("============================")
    success = test_openrouter_api_key()
    print("\n✅ Test completed successfully" if success else "\n❌ Test failed")
