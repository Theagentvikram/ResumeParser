#!/usr/bin/env python3
"""
Test script for PDF extraction and analysis
"""
import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import PDF extraction service
try:
    from backend.services.pdf_service import extract_text_from_pdf
except ImportError:
    print("Error importing PDF service, trying relative import...")
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from backend.services.pdf_service import extract_text_from_pdf

# Import OpenRouter service
try:
    from backend.services.openrouter_service import analyze_resume_with_openrouter
except ImportError:
    print("Error importing OpenRouter service, trying relative import...")
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from backend.services.openrouter_service import analyze_resume_with_openrouter

def test_pdf_extraction_and_analysis(pdf_path):
    """Test PDF extraction and analysis"""
    print(f"Testing PDF extraction and analysis with file: {pdf_path}")
    
    # Check if the file exists
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} does not exist")
        return False
    
    # Extract text from PDF
    try:
        print("Extracting text from PDF...")
        resume_text = extract_text_from_pdf(pdf_path)
        
        # Print extracted text stats
        print(f"Extracted text length: {len(resume_text)} characters")
        print(f"Text sample: {resume_text[:200].replace(chr(10), ' ')}...")
        
        # Check if we got enough text
        if not resume_text or len(resume_text.strip()) < 100:
            print("Error: Failed to extract meaningful text from PDF")
            return False
        
        # Analyze the resume text
        print("\nAnalyzing resume text with OpenRouter API...")
        analysis_result = analyze_resume_with_openrouter(resume_text)
        
        # Print analysis result
        print("\n--- Analysis Result ---")
        print(json.dumps(analysis_result, indent=2))
        
        return True
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Check if a PDF file path was provided
    if len(sys.argv) < 2:
        print("Usage: python test-pdf-extraction.py <path_to_pdf>")
        sys.exit(1)
    
    # Get the PDF file path
    pdf_path = sys.argv[1]
    
    # Test PDF extraction and analysis
    success = test_pdf_extraction_and_analysis(pdf_path)
    
    # Print result
    if success:
        print("\n✅ PDF extraction and analysis successful")
    else:
        print("\n❌ PDF extraction and analysis failed")
