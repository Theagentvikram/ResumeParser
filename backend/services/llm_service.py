import os
import requests
import json
import random
from typing import Dict, List, Any
import httpx

# Get HF API key from environment variable
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-large"

async def get_resume_summary(resume_text: str) -> Dict[str, Any]:
    """
    Get a summary of a resume using Hugging Face's Inference API
    
    Args:
        resume_text: Text extracted from the resume
        
    Returns:
        Dictionary with summary, skills, experience, educationLevel, and category
    """
    try:
        # Use real API if key is available, else use mock data
        if HF_API_KEY:
            return await generate_summary_with_api(resume_text)
        else:
            print("WARNING: No HF API key found. Using mock data.")
            return generate_mock_summary(resume_text)
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        # Fallback to mock data
        return generate_mock_summary(resume_text)

async def generate_summary_with_api(resume_text: str) -> Dict[str, Any]:
    """Generate resume summary using Hugging Face API"""
    
    # Create prompts for each aspect of the resume
    summary_prompt = f"Summarize this resume in 2-3 sentences: {resume_text[:4000]}"
    skills_prompt = f"List the top skills from this resume as comma-separated values: {resume_text[:4000]}"
    experience_prompt = f"Estimate the years of experience from this resume (return just a number): {resume_text[:4000]}"
    education_prompt = f"What is the highest education level in this resume? Choose from: High School, Associate's, Bachelor's, Master's, PhD: {resume_text[:4000]}"
    category_prompt = f"What job category does this resume best fit? Choose from: Software Engineer, Data Scientist, Web Developer, Database Administrator, DevOps Engineer: {resume_text[:4000]}"
    
    # Create HTTP client
    async with httpx.AsyncClient() as client:
        # Make parallel requests
        summary_task = client.post(
            HF_API_URL,
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            json={"inputs": summary_prompt}
        )
        
        skills_task = client.post(
            HF_API_URL,
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            json={"inputs": skills_prompt}
        )
        
        experience_task = client.post(
            HF_API_URL,
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            json={"inputs": experience_prompt}
        )
        
        education_task = client.post(
            HF_API_URL,
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            json={"inputs": education_prompt}
        )
        
        category_task = client.post(
            HF_API_URL,
            headers={"Authorization": f"Bearer {HF_API_KEY}"},
            json={"inputs": category_prompt}
        )
        
        # Gather responses
        summary_response = await summary_task
        skills_response = await skills_task
        experience_response = await experience_task
        education_response = await education_task
        category_response = await category_task
        
        # Process responses
        summary = summary_response.json()[0]["generated_text"]
        skills_text = skills_response.json()[0]["generated_text"]
        skills = [skill.strip() for skill in skills_text.split(",") if skill.strip()]
        
        # Handle experience (ensure it's a number)
        experience_text = experience_response.json()[0]["generated_text"]
        try:
            # Extract first number from the response
            import re
            experience_match = re.search(r'\d+', experience_text)
            experience = int(experience_match.group()) if experience_match else random.randint(1, 7)
        except:
            experience = random.randint(1, 7)
        
        education = education_response.json()[0]["generated_text"]
        category = category_response.json()[0]["generated_text"]
        
        # Normalize education level
        education_mapping = {
            "high school": "High School",
            "associate": "Associate's",
            "bachelor": "Bachelor's",
            "master": "Master's",
            "phd": "PhD",
            "doctorate": "PhD"
        }
        
        for key, value in education_mapping.items():
            if key.lower() in education.lower():
                education = value
                break
        else:
            education = "Bachelor's"  # Default
        
        # Ensure category is one of the expected values
        valid_categories = [
            "Software Engineer", "Data Scientist", "Web Developer",
            "Database Administrator", "DevOps Engineer"
        ]
        
        if category not in valid_categories:
            # Find closest match
            for valid_cat in valid_categories:
                if valid_cat.lower() in category.lower():
                    category = valid_cat
                    break
            else:
                category = "Software Engineer"  # Default
        
        return {
            "summary": summary,
            "skills": skills[:10],  # Limit to 10 skills
            "experience": experience,
            "educationLevel": education,
            "category": category
        }

def generate_mock_summary(resume_text: str) -> Dict[str, Any]:
    """Generate mock resume summary for testing"""
    skill_sets = [
        ["JavaScript", "React", "Node.js", "TypeScript", "HTML", "CSS"],
        ["Python", "TensorFlow", "PyTorch", "Data Science", "Machine Learning"],
        ["Java", "Spring Boot", "Hibernate", "Microservices", "REST API"],
        ["SQL", "PostgreSQL", "MongoDB", "Database Design", "ETL"],
        ["AWS", "Docker", "Kubernetes", "CI/CD", "DevOps"]
    ]
    
    summary_templates = [
        "Experienced software developer with strong skills in frontend and backend development. Has worked on complex web applications and demonstrates excellent problem-solving abilities.",
        "Data scientist with expertise in machine learning and statistical analysis. Proven track record of implementing ML models in production environments.",
        "Full-stack developer with focus on modern JavaScript frameworks. Experienced in building responsive, high-performance web applications.",
        "Database specialist with deep knowledge of SQL and NoSQL systems. Skilled in data modeling, optimization, and ETL processes.",
        "DevOps engineer with cloud expertise. Experienced in building and maintaining scalable infrastructure on major cloud platforms."
    ]
    
    categories = ["Software Engineer", "Data Scientist", "Web Developer", "Database Administrator", "DevOps Engineer"]
    education_levels = ["High School", "Associate's", "Bachelor's", "Master's", "PhD"]
    
    # Pick a random index to keep the mock data consistent
    idx = random.randint(0, len(skill_sets) - 1)
    
    return {
        "summary": summary_templates[idx],
        "skills": skill_sets[idx],
        "experience": random.randint(1, 8),
        "educationLevel": education_levels[random.randint(0, len(education_levels) - 1)],
        "category": categories[idx]
    } 