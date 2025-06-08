#!/usr/bin/env python3
"""
Test script for the resume analysis API endpoint
"""
import requests
import json

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

def test_analyze_resume():
    """Test the resume analysis API endpoint"""
    print("Testing resume analysis API endpoint...")
    
    # API endpoint
    url = "http://localhost:8000/api/resumes/analyze"
    
    # The API expects form data with a text field
    # Try both application/x-www-form-urlencoded and multipart/form-data
    
    # Method 1: Using form data (application/x-www-form-urlencoded)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # Create form data
    form_data = {"text": TEST_RESUME}
    
    print("Using application/x-www-form-urlencoded format")
    print(f"Form data: {form_data}")
    print(f"Headers: {headers}")
    
    # Send the request
    try:
        print("Sending request to API...")
        response = requests.post(url, data=form_data, headers=headers, timeout=60)
        
        # Check if the request was successful
        if response.status_code == 200:
            print("✅ Success! Received response from API")
            
            # Parse the response
            result = response.json()
            
            # Print the result
            print("\n--- API Response ---")
            print(json.dumps(result, indent=2))
            
            # Check if the result has the expected fields
            expected_fields = ["skills", "experience", "educationLevel", "summary", "category"]
            missing_fields = [field for field in expected_fields if field not in result]
            
            if not missing_fields:
                print("\n✅ All expected fields are present in the response")
            else:
                print(f"\n❌ Missing fields in the response: {missing_fields}")
            
            return True
        else:
            print(f"❌ API call failed with status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error calling API: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔍 ResuMatch API Analysis Test 🔍")
    print("===============================")
    
    # Test the resume analysis API endpoint
    success = test_analyze_resume()
    
    if success:
        print("\n✅ Test completed successfully")
    else:
        print("\n❌ Test failed")
