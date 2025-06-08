#!/usr/bin/env python3
import requests
import json
import sys

# Simple test script to verify the LLM resume analysis is working

# Test resume text (simple version for quick testing)
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

def test_resume_analysis():
    """Test the resume analysis endpoint with a simple resume"""
    print("Testing resume analysis with local LLM...")
    
    # First check the model status
    try:
        response = requests.get("http://localhost:8000/api/model/status")
        status = response.json()
        print(f"Model status: {json.dumps(status, indent=2)}")
        
        if status.get("mode") != "llama_cpp" or status.get("using_fallback"):
            print("WARNING: Not using local LLM mode!")
    except Exception as e:
        print(f"Error checking model status: {str(e)}")
        return False
    
    # Now test the resume analysis
    try:
        # Send the text as a JSON body
        response = requests.post(
            "http://localhost:8000/resumes/analyze",
            json={"text": TEST_RESUME}
        )
        
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            print(response.text)
            return False
        
        result = response.json()
        print("\nAnalysis result:")
        print(json.dumps(result, indent=2))
        
        # Check if the result looks like it came from an LLM (more detailed than regex)
        if len(result.get("skills", [])) >= 3 and len(result.get("summary", "")) > 50:
            print("\n Success! The analysis appears to be from the LLM")
            return True
        else:
            print("\n The analysis looks too simple, might be from regex")
            return False
            
    except Exception as e:
        print(f"Error testing resume analysis: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_resume_analysis()
    sys.exit(0 if success else 1)
