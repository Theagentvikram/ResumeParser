#!/usr/bin/env python3
"""
Simple direct test of OpenRouter API with Mistral model
"""
import requests
import json

# Use the API key directly
API_KEY = "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"
MODEL = "mistralai/mistral-7b-instruct:free"

# OpenRouter API URL
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Test resume text
TEST_RESUME = """
John Doe
Software Engineer

EXPERIENCE:
Senior Software Engineer, ABC Tech (2018-Present)
- Developed and maintained cloud-based applications using Python and AWS
- Led a team of 5 developers on a major project

Software Developer, XYZ Solutions (2015-2018)
- Built web applications using React and Node.js
- Implemented CI/CD pipelines

EDUCATION:
Master of Computer Science, Stanford University (2015)
Bachelor of Engineering, MIT (2013)

SKILLS:
Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes, CI/CD
"""

def test_openrouter_api():
    """Test the OpenRouter API with the Mistral model"""
    print(f"Testing OpenRouter API with model: {MODEL}")
    
    # Set up headers
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://resumatch.app",
        "X-Title": "ResuMatch"
    }
    
    print(f"Using API key: {API_KEY}")
    
    # Create a prompt for resume analysis
    system_prompt = "You are an AI assistant that specializes in resume analysis."
    
    user_prompt = f"""Analyze this resume and extract key information as JSON:

{TEST_RESUME}

Extract: summary (1-2 sentences), skills (list), experience (years as number), educationLevel (highest degree), category (job field)."""
    
    # Prepare the payload
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.1
    }
    
    try:
        # Make the API call
        print("Sending request to OpenRouter API...")
        response = requests.post(API_URL, headers=headers, json=payload)
        
        # Print full response for debugging
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        print(f"Response body: {response.text}")
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse the response
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
                return False
        else:
            print(f"\n❌ API call failed with status code {response.status_code}")
            print(response.text)
            return False
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 OpenRouter API Simple Test with Mistral 7B 🔍")
    print("===============================================")
    success = test_openrouter_api()
    print("\n✅ Test completed successfully" if success else "\n❌ Test failed")
