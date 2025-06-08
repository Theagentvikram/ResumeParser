#!/usr/bin/env python3
"""
Simple test script for OpenRouter API key
"""
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
API_KEY = os.getenv("OPENROUTER_API_KEY")
print(f"API key from .env: {API_KEY[:10]}...{API_KEY[-5:]} (length: {len(API_KEY)})")

# Test different API key formats
def test_api_key(key, description):
    print(f"\n--- Testing {description} ---")
    print(f"Key: {key[:10]}...{key[-5:]} (length: {len(key)})")
    
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {"Authorization": f"Bearer {key}"}
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

# Test with the original key
original_success = test_api_key(API_KEY, "Original API key")

# Test with a modified key (if needed)
if not original_success:
    print("\nAPI key test failed. Let's try a fallback approach.")
    
    # Try with a hardcoded key for testing
    hardcoded_key = "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"
    hardcoded_success = test_api_key(hardcoded_key, "Hardcoded API key")
    
    if not hardcoded_success:
        print("\n❌ All API key tests failed. The API key may have expired or been revoked.")
        print("Please generate a new API key at https://openrouter.ai/keys")
    else:
        print("\n✅ Hardcoded API key test succeeded!")
else:
    print("\n✅ Original API key test succeeded!")
