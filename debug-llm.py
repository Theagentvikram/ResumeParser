#!/usr/bin/env python3
import requests
import json
import sys
import os

# Simple debug script to test different ways of calling the resume analysis API

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

def check_model_status():
    """Check the model status"""
    try:
        response = requests.get("http://localhost:8000/api/model/status")
        status = response.json()
        print(f"Model status: {json.dumps(status, indent=2)}")
        return status
    except Exception as e:
        print(f"Error checking model status: {str(e)}")
        return None

def test_method_1():
    """Test using JSON body with text field"""
    print("\n--- Testing Method 1: JSON body with text field ---")
    try:
        response = requests.post(
            "http://localhost:8000/resumes/analyze",
            json={"text": TEST_RESUME}
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_method_2():
    """Test using form data with text field"""
    print("\n--- Testing Method 2: Form data with text field ---")
    try:
        response = requests.post(
            "http://localhost:8000/resumes/analyze",
            data={"text": json.dumps({"text": TEST_RESUME})}
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_method_3():
    """Test using multipart form with file field"""
    print("\n--- Testing Method 3: Multipart form with file field ---")
    try:
        # Create a temporary file with the resume text
        temp_file_path = "temp_resume.txt"
        with open(temp_file_path, "w") as f:
            f.write(TEST_RESUME)
        
        # Send the file
        with open(temp_file_path, "rb") as f:
            response = requests.post(
                "http://localhost:8000/resumes/analyze",
                files={"file": ("resume.txt", f, "text/plain")}
            )
        
        # Clean up
        os.remove(temp_file_path)
        
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        # Clean up in case of error
        if os.path.exists("temp_resume.txt"):
            os.remove("temp_resume.txt")
        return False

def test_method_4():
    """Test using multipart form with both file and text fields"""
    print("\n--- Testing Method 4: Multipart form with both file and text fields ---")
    try:
        response = requests.post(
            "http://localhost:8000/resumes/analyze",
            files={"file": (None, "", "application/octet-stream")},
            data={"text": TEST_RESUME}
        )
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 ResuMatch LLM API Debug Script 🔍")
    print("====================================")
    
    # Check model status
    status = check_model_status()
    if not status:
        print("❌ Failed to check model status")
        sys.exit(1)
    
    # Try different methods
    methods = [
        test_method_1,
        test_method_2,
        test_method_3,
        test_method_4
    ]
    
    success = False
    for method in methods:
        if method():
            print(f"\n✅ Success with {method.__name__}!")
            success = True
            break
        else:
            print(f"❌ Failed with {method.__name__}")
    
    if not success:
        print("\n❌ All methods failed")
        sys.exit(1)
    else:
        sys.exit(0)
