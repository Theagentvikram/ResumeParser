#!/usr/bin/env python3
"""
Test script using the exact format from OpenRouter API documentation
"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
MODEL = "mistralai/mistral-7b-instruct:free"

print(f"Using API key: {API_KEY[:10]}...{API_KEY[-5:]}")
print(f"API key length: {len(API_KEY)} characters")

def test_openrouter_api():
    """Test OpenRouter API using the exact format from their documentation"""
    print("Testing OpenRouter API with documentation example...")
    
    # OpenRouter API URL
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Headers exactly as in documentation
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Payload exactly as in documentation
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, who are you?"}
        ]
    }
    
    print("Sending request to OpenRouter API...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Success! Received response from OpenRouter API")
            
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
    print("🔍 OpenRouter API Documentation Test 🔍")
    print("=====================================")
    success = test_openrouter_api()
    print("\n✅ Test completed successfully" if success else "\n❌ Test failed")
