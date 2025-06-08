#!/usr/bin/env python3
"""
Direct test of OpenRouter API with Mistral model
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Use the correct API key directly to ensure it works
API_KEY = "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"
MODEL = "mistralai/mistral-7b-instruct:free"

# Print the API key being used
print(f"Using API key directly: {API_KEY[:10]}...{API_KEY[-5:]}")
print(f"API key length: {len(API_KEY)} characters")

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
    
    # Set up the headers with authentication - simplified as in updated openrouter_service.py
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    print("Using simplified headers as in updated openrouter_service.py")
    print(f"Authorization header: {headers['Authorization']}")
    print(f"Content-Type: {headers['Content-Type']}")
    
    
    
    print(f"Using API key: {API_KEY[:10]}...{API_KEY[-5:]}")
    print(f"Authorization header: Bearer {API_KEY[:10]}...{API_KEY[-5:]}")
    
    
    # Create a prompt for resume analysis
    system_prompt = "You are an AI assistant that specializes in resume analysis. Extract key information from resumes accurately."
    
    user_prompt = f"""Analyze the following resume text and extract key information.
    
RESUME TEXT:
{TEST_RESUME}

Based on the resume above, extract and return ONLY the following information in JSON format:

1. summary: A professional summary of the candidate (3-4 sentences)
2. skills: An array of professional skills mentioned in the resume (technical, soft skills, tools, etc.)
3. experience: The years of professional experience (as a number)
4. educationLevel: The highest level of education (High School, Associate's, Bachelor's, Master's, PhD, or Other)
5. category: The job category that best matches this resume (e.g., Software Engineering, Data Science, Marketing, etc.)

Format your response as a valid JSON object with these five keys. DO NOT include any explanations before or after the JSON.
"""
    
    # Prepare the payload
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "max_tokens": 500,
        "temperature": 0.1,
        "top_p": 0.95
    }
    
    try:
        # Make the API call
        print("Sending request to OpenRouter API...")
        response = requests.post(API_URL, headers=headers, json=payload)
        
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
                
                # Try to parse as JSON
                try:
                    json_start = generated_text.find("{")
                    json_end = generated_text.rfind("}")
                    
                    if json_start != -1 and json_end != -1:
                        json_str = generated_text[json_start:json_end+1]
                        parsed_json = json.loads(json_str)
                        
                        print("\n--- Parsed JSON Result ---")
                        print(json.dumps(parsed_json, indent=2))
                        return True
                    else:
                        print("\n❌ No JSON found in response")
                        return False
                except json.JSONDecodeError as e:
                    print(f"\n❌ Failed to parse JSON: {e}")
                    return False
            else:
                print("\n❌ Unexpected response format")
                print(result)
                return False
        else:
            print(f"\n❌ API call failed with status code {response.status_code}")
            print(response.text)
            return False
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 OpenRouter API Direct Test with Mistral 7B 🔍")
    print("===============================================")
    success = test_openrouter_api()
    print("\n✅ Test completed successfully" if success else "\n❌ Test failed")
