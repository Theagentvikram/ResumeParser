#!/usr/bin/env python3
"""
Check available models on OpenRouter
"""
import requests
import json

# API key from the project
API_KEY = "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"

def check_openrouter_models():
    """Check available models on OpenRouter"""
    print("Checking available models on OpenRouter...")
    
    # API endpoint for models
    url = "https://openrouter.ai/api/v1/models"
    
    # Set up headers with authentication
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # Send the request
        response = requests.get(url, headers=headers)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("✅ Success! Received response from OpenRouter API")
            
            # Parse the response
            models = response.json()
            
            # Print the available models
            print("\n--- Available Models ---")
            for model in models.get("data", []):
                print(f"ID: {model.get('id')}")
                print(f"Name: {model.get('name')}")
                print(f"Context Length: {model.get('context_length')}")
                print(f"Pricing: {model.get('pricing', {}).get('prompt')} per prompt token, {model.get('pricing', {}).get('completion')} per completion token")
                print("---")
            
            # Find free models
            free_models = [model for model in models.get("data", []) if "free" in model.get("id", "").lower()]
            if free_models:
                print("\n--- Free Models ---")
                for model in free_models:
                    print(f"ID: {model.get('id')}")
                    print(f"Name: {model.get('name')}")
                    print("---")
            
            return models
        else:
            print(f"❌ API call failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error calling API: {str(e)}")
        return None

if __name__ == "__main__":
    print("🔍 OpenRouter Models Check 🔍")
    print("============================")
    
    # Check available models
    models = check_openrouter_models()
    
    if models:
        # Save models to a file for reference
        with open("openrouter-models.json", "w") as f:
            json.dump(models, f, indent=2)
        print("\n✅ Models saved to openrouter-models.json")
