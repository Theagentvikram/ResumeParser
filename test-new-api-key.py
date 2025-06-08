#!/usr/bin/env python3
"""
Test script for the new OpenRouter API key
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables with force reload
load_dotenv(override=True)

# Print all environment variables for debugging
print("Environment variables:")
for key, value in os.environ.items():
    if key.startswith("OPENROUTER"):
        print(f"  {key}: {value[:10]}...{value[-5:]}")

# Get API key from environment
API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("OPENROUTER_MODEL", "mistralai/mistral-7b-instruct:free")

print(f"Testing new API key: {API_KEY[:10]}...{API_KEY[-5:]}")
print(f"API key length: {len(API_KEY)} characters")
print(f"Using model: {MODEL}")

def test_openrouter_api():
    """Test the OpenRouter API with the new API key"""
    # OpenRouter API URL
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Set up headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Prepare a simple payload
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, who are you?"}
        ]
    }
    
    print("\nSending request to OpenRouter API...")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success! API key is working correctly.")
            
            # Extract the generated text
            if "choices" in result and len(result["choices"]) > 0:
                generated_text = result["choices"][0]["message"]["content"]
                
                print("\n--- Generated Response ---")
                print(generated_text)
                return True
            else:
                print("\n❌ Unexpected response format")
                print(result)
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
    success = test_openrouter_api()
    print("\n✅ Test completed successfully" if success else "\n❌ Test failed")
