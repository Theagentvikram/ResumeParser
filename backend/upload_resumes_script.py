import os
import requests
import json
from pathlib import Path
import asyncio # For async API calls if needed

# Adjust this path if your 'Resumes' folder is not directly parallel to 'backend'
RESUMES_SOURCE_DIR = Path("../Resumes")
BACKEND_UPLOAD_URL = "http://localhost:8000/api/resumes/upload"
BACKEND_ANALYZE_URL = "http://localhost:8000/api/resumes/analyze"

async def upload_single_resume(file_path: Path):
    print(f"Processing {file_path.name}...")

    # Step 1: Extract text and get metadata using the analyze endpoint
    try:
        if file_path.suffix.lower() == ".pdf":
            # For PDF, we'll send the file directly to the analyze endpoint
            with open(file_path, "rb") as f:
                files = {'file': (file_path.name, f, 'application/pdf')}
                analyze_response = requests.post(BACKEND_ANALYZE_URL, files=files)
        elif file_path.suffix.lower() == ".txt":
            # For TXT, read content and send as text
            with open(file_path, "r", encoding="utf-8") as f:
                text_content = f.read()
            analyze_response = requests.post(BACKEND_ANALYZE_URL, json={"text": text_content})
        else:
            print(f"Skipping {file_path.name}: Unsupported file type for analysis.")
            return

        analyze_response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        metadata = analyze_response.json()
        print(f"Analyzed {file_path.name}. Metadata: {metadata.get('skills')[:3]}...")

    except requests.exceptions.RequestException as e:
        print(f"Error analyzing {file_path.name} with backend: {e}")
        print("Falling back to dummy metadata for upload.")
        # Fallback to dummy metadata if analysis fails
        metadata = {
            "skills": ["Default Skill 1", "Default Skill 2"],
            "experience": "0",
            "educationLevel": "Unknown",
            "summary": f"Could not analyze resume {file_path.name}. Default summary.",
            "category": "General"
        }
    except json.JSONDecodeError:
        print(f"Error decoding JSON from analyze response for {file_path.name}. Falling back to dummy metadata.")
        metadata = {
            "skills": ["Default Skill 1", "Default Skill 2"],
            "experience": "0",
            "educationLevel": "Unknown",
            "summary": f"Could not analyze resume {file_path.name}. Default summary.",
            "category": "General"
        }

    # Step 2: Upload the resume with extracted/dummy metadata
    try:
        with open(file_path, "rb") as f:
            files = {'file': (file_path.name, f, 'application/pdf' if file_path.suffix.lower() == '.pdf' else 'text/plain')}
            data = {'metadata': json.dumps(metadata)}
            upload_response = requests.post(BACKEND_UPLOAD_URL, files=files, data=data)
            upload_response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            print(f"Successfully uploaded {file_path.name}")
            print(upload_response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error uploading {file_path.name} to backend: {e}")

async def main():
    if not RESUMES_SOURCE_DIR.exists():
        print(f"Error: The directory '{RESUMES_SOURCE_DIR.resolve()}' does not exist.")
        print("Please ensure your 'Resumes' folder is directly in the project root.")
        return

    print(f"Scanning for resumes in: {RESUMES_SOURCE_DIR.resolve()}")
    resume_files = [f for f in RESUMES_SOURCE_DIR.iterdir() if f.is_file() and f.suffix.lower() in ['.pdf', '.txt']]

    if not resume_files:
        print(f"No PDF or TXT resume files found in '{RESUMES_SOURCE_DIR.resolve()}'.")
        return

    for resume_file in resume_files:
        await upload_single_resume(resume_file)
    print("Resume upload process completed.")

if __name__ == "__main__":
    # Ensure event loop is run for async functions
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "cannot run non-async" in str(e):
            # Fallback for environments that don't support direct asyncio.run in global scope easily
            print("Running in a synchronous context. Using old loop style...")
            loop = asyncio.get_event_loop()
            loop.run_until_complete(main())
            loop.close()
        else:
            raise 