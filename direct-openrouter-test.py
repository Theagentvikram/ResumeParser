#!/usr/bin/env python3
"""
Direct test of OpenRouter API with hardcoded credentials
This will help us identify if the issue is with the API key or something else
"""
import requests
import json
import os

# Hardcode the API key directly to ensure it's correct
API_KEY = "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"
MODEL = "mistralai/mistral-small-3.1-24b-instruct:free"
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Test resume text
TEST_RESUME = """
John Doe
Software Engineer

EXPERIENCE
Senior Software Engineer
ABC Tech, 2020-Present
- Developed and maintained cloud-based applications using Python and AWS
- Led a team of 5 engineers to deliver a new product feature
- Implemented CI/CD pipelines for automated testing and deployment

Software Engineer
XYZ Corp, 2017-2020
- Built web applications using React and Node.js
- Collaborated with product managers to define requirements
- Optimized database queries for improved performance

EDUCATION
Stanford University
Master of Science in Computer Science, 2017

Massachusetts Institute of Technology
Bachelor of Science in Computer Science, 2015

SKILLS
Programming: Python, JavaScript, Java
Web: React, Node.js, HTML, CSS
Cloud: AWS, Docker, Kubernetes
Tools: Git, Jenkins, JIRA
"""

def test_openrouter():
    """Test the OpenRouter API directly with hardcoded credentials"""
    print(f"Testing OpenRouter API with model: {MODEL}")
    print(f"API key: {API_KEY[:10]}...{API_KEY[-5:]}")
    
    # Set up headers with all possible authentication methods
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://resumatch.app",
        "X-Title": "ResuMatch",
        "OpenAI-Organization": "org-",
        "User-Agent": "ResuMatch/1.0"
    }
    
    # Create a simple system and user prompt
    system_prompt = "You are an AI assistant that specializes in resume analysis."
    
    user_prompt = f"""Analyze this resume and extract key information:

{TEST_RESUME}

Return ONLY a JSON object with these fields:
- summary: A brief professional summary
- skills: Array of skills mentioned
- experience: Years of experience (number)
- educationLevel: Highest education level
- category: Job category

Format as valid JSON with no explanations."""
    
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
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        # Print response details
        print(f"Response status code: {response.status_code}")
        print(f"Response headers: {response.headers}")
        
        if response.status_code == 200:
            # Success! Parse the response
            result = response.json()
            print("\n✅ Success! Received response from OpenRouter API")
            
            # Extract the generated text
            if "choices" in result and len(result["choices"]) > 0:
                generated_text = result["choices"][0]["message"]["content"]
                print("\n--- Generated Response ---")
                print(generated_text)
                
                # Try to parse the JSON
                try:
                    parsed_json = json.loads(generated_text)
                    print("\n--- Parsed JSON Result ---")
                    print(json.dumps(parsed_json, indent=2))
                except json.JSONDecodeError:
                    print("\n❌ Could not parse response as JSON")
            else:
                print("\n❌ Unexpected response format")
                print(result)
        else:
            # Error
            print(f"\n❌ API call failed with status code {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🔍 Direct OpenRouter API Test 🔍")
    print("===============================")
    test_openrouter()
