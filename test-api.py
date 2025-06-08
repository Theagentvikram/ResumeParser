#!/usr/bin/env python3
import requests
import json

# Simple test resume
test_resume = """
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

# Test the model status endpoint
print("Checking model status...")
response = requests.get("http://localhost:8000/api/model/status")
status = response.json()
print(f"Status: {json.dumps(status, indent=2)}")

# Test the resume analysis endpoint with plain text
print("\nTesting resume analysis with text input...")
response = requests.post(
    "http://localhost:8000/resumes/analyze", 
    json={"text": test_resume}
)

if response.status_code == 200:
    result = response.json()
    print(f"Success! Result: {json.dumps(result, indent=2)}")
    
    # Check if it looks like LLM output
    if len(result.get("summary", "")) > 50:
        print("\nThis appears to be LLM-generated content (detailed summary)")
    else:
        print("\nThis might be regex-generated (simple summary)")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
