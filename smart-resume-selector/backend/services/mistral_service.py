#!/usr/bin/env python3
"""
Mistral LLM Service for Smart Resume Selector
Uses Mistral-7B-Instruct via Ollama for summarizing structured resume data
"""
import os
import json
import logging
import requests
from typing import Dict, List, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mistral-service")

class MistralService:
    """
    Service for interacting with Mistral-7B-Instruct via Ollama
    Handles summarization of structured resume data
    """
    
    def __init__(self, ollama_base_url: str = "http://localhost:11434"):
        """
        Initialize the Mistral service
        
        Args:
            ollama_base_url: Base URL for Ollama API
        """
        self.ollama_base_url = ollama_base_url
        self.model_name = "mistral:7b-instruct-v0.2"
        self.api_endpoint = f"{ollama_base_url}/api/generate"
        
        # Check if Ollama is available
        self.is_available = self._check_availability()
        if not self.is_available:
            logger.warning("Ollama is not available. LLM summarization will not work.")
        else:
            logger.info(f"Mistral service initialized with model: {self.model_name}")
    
    def _check_availability(self) -> bool:
        """Check if Ollama is available and has the Mistral model"""
        try:
            # Try to ping Ollama
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code != 200:
                logger.error(f"Ollama server not available at {self.ollama_base_url}")
                return False
            
            # Check if Mistral model is available
            models = response.json().get("models", [])
            if not any(model.get("name", "").startswith("mistral") for model in models):
                logger.warning("Mistral model not found in Ollama. Will attempt to pull it when needed.")
            
            return True
        except Exception as e:
            logger.error(f"Error checking Ollama availability: {str(e)}")
            return False
    
    def _ensure_model_available(self) -> bool:
        """Ensure the Mistral model is available, pulling it if needed"""
        if not self.is_available:
            logger.warning("Ollama is not available. Cannot ensure model availability.")
            return False
        
        try:
            # Check if model exists
            response = requests.get(f"{self.ollama_base_url}/api/tags")
            if response.status_code != 200:
                logger.error("Failed to get model list from Ollama")
                return False
            
            models = response.json().get("models", [])
            if any(model.get("name", "").startswith("mistral") for model in models):
                return True
            
            # Pull the model if not available
            logger.info(f"Pulling Mistral model: {self.model_name}")
            pull_response = requests.post(
                f"{self.ollama_base_url}/api/pull",
                json={"name": self.model_name}
            )
            
            if pull_response.status_code != 200:
                logger.error(f"Failed to pull Mistral model: {pull_response.text}")
                return False
            
            logger.info("Mistral model pulled successfully")
            return True
        except Exception as e:
            logger.error(f"Error ensuring model availability: {str(e)}")
            return False
    
    def _format_structured_data(self, data: Dict[str, Any]) -> str:
        """Format structured resume data for LLM input"""
        # Format skills as comma-separated list
        skills_str = ", ".join(data.get("skills", []))
        
        # Format education
        education_list = data.get("education", [])
        education_str = ""
        for edu in education_list:
            degree = edu.get("degree", "")
            institution = edu.get("institution", "")
            year = edu.get("year", "")
            education_str += f"{degree} at {institution} {f'({year})' if year else ''}\n"
        
        # Format experience
        experience_list = data.get("experience", [])
        experience_str = ""
        for exp in experience_list:
            title = exp.get("title", "")
            company = exp.get("company", "")
            start_year = exp.get("start_year", "")
            end_year = exp.get("end_year", "")
            date_range = ""
            if start_year and end_year:
                date_range = f"({start_year} - {end_year if end_year != 2025 else 'Present'})"
            experience_str += f"{title} at {company} {date_range}\n"
        
        # Format projects
        projects_list = data.get("projects", [])
        projects_str = ""
        for proj in projects_list:
            title = proj.get("title", "")
            description = proj.get("description", "")
            projects_str += f"{title}: {description}\n"
        
        # Combine all formatted data
        formatted_data = f"""Name: {data.get('name', 'Unknown')}
Email: {data.get('email', 'Unknown')}
Phone: {data.get('phone', 'Unknown')}

Skills: {skills_str}

Experience:
{experience_str}

Education:
{education_str}"""

        # Add projects if available
        if projects_str:
            formatted_data += f"""
Projects:
{projects_str}"""
        
        return formatted_data
    
    def summarize_resume(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize structured resume data using Mistral
        
        Args:
            structured_data: Structured resume data from PDF extractor
            
        Returns:
            Dictionary with summary, category, and other extracted information
        """
        if not self.is_available:
            logger.warning("Ollama is not available. Using fallback summarization.")
            return self._fallback_summarization(structured_data)
        
        # Ensure model is available
        if not self._ensure_model_available():
            logger.warning("Failed to ensure Mistral model availability. Using fallback summarization.")
            return self._fallback_summarization(structured_data)
        
        try:
            # Format structured data for LLM input
            formatted_data = self._format_structured_data(structured_data)
            
            # Create prompt for Mistral
            prompt = f"""<s>[INST]Summarize this resume data in a concise way:

```
{formatted_data}
```

Provide a JSON response with the following fields:
1. summary: A 1-2 sentence professional summary
2. category: The job category/field (e.g., Software Engineering, Data Science, Marketing)
3. key_skills: List of 5 most important skills
4. experience_level: Junior, Mid-level, or Senior based on experience
5. match_keywords: List of 5-10 keywords that recruiters might search for to find this candidate[/INST]</s>
"""
            
            # Call Ollama API
            response = requests.post(
                self.api_endpoint,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.1,
                    "max_tokens": 500
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Error from Ollama API: {response.text}")
                return self._fallback_summarization(structured_data)
            
            # Extract response
            result = response.json()
            generated_text = result.get("response", "")
            
            # Parse JSON from response
            try:
                # Extract JSON object from the response
                json_text = generated_text.strip()
                
                # If the response is not a valid JSON, try to extract it
                if not json_text.startswith('{'):
                    json_match = json_text.find('{')
                    if json_match != -1:
                        json_text = json_text[json_match:]
                
                # If the JSON is incomplete, try to complete it
                bracket_diff = json_text.count('{') - json_text.count('}')
                if bracket_diff > 0:
                    json_text += '}' * bracket_diff
                
                # Parse the JSON
                summary_data = json.loads(json_text)
                
                # Ensure all expected fields are present
                summary_data = {
                    "summary": summary_data.get("summary", "Professional with relevant skills and experience."),
                    "category": summary_data.get("category", "Professional"),
                    "key_skills": summary_data.get("key_skills", structured_data.get("skills", [])[:5]),
                    "experience_level": summary_data.get("experience_level", "Mid-level"),
                    "match_keywords": summary_data.get("match_keywords", []),
                    "total_experience_years": structured_data.get("total_experience_years", 0)
                }
                
                # Ensure key_skills and match_keywords are lists
                if not isinstance(summary_data["key_skills"], list):
                    summary_data["key_skills"] = [k.strip() for k in str(summary_data["key_skills"]).split(",")]
                
                if not isinstance(summary_data["match_keywords"], list):
                    summary_data["match_keywords"] = [k.strip() for k in str(summary_data["match_keywords"]).split(",")]
                
                logger.info("Successfully summarized resume with Mistral")
                return summary_data
            
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error parsing Mistral response as JSON: {str(e)}")
                logger.debug(f"Raw response: {generated_text[:200]}...")
                return self._fallback_summarization(structured_data)
                
        except Exception as e:
            logger.error(f"Error summarizing resume with Mistral: {str(e)}")
            return self._fallback_summarization(structured_data)
    
    def _fallback_summarization(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fallback method to generate a summary without using LLM
        
        Args:
            structured_data: Structured resume data from PDF extractor
            
        Returns:
            Dictionary with summary and other information
        """
        logger.info("Using fallback summarization method")
        
        # Extract basic information
        name = structured_data.get("name", "Unknown")
        skills = structured_data.get("skills", [])
        experience = structured_data.get("experience", [])
        education = structured_data.get("education", [])
        total_years = structured_data.get("total_experience_years", 0)
        
        # Determine experience level
        experience_level = "Junior"
        if total_years > 5:
            experience_level = "Senior"
        elif total_years > 2:
            experience_level = "Mid-level"
        
        # Determine job category based on skills
        category = "Professional"
        tech_keywords = ["python", "javascript", "java", "react", "angular", "node", "web", "frontend", "backend", "fullstack", "software", "developer", "engineer"]
        data_keywords = ["data", "analytics", "analysis", "science", "machine learning", "ai", "artificial intelligence", "statistics", "statistical", "python", "r", "sql", "tableau", "powerbi"]
        design_keywords = ["design", "ui", "ux", "user interface", "user experience", "graphic", "adobe", "photoshop", "illustrator", "figma", "sketch"]
        
        # Count keyword occurrences in skills
        tech_count = sum(1 for skill in skills if any(kw in skill.lower() for kw in tech_keywords))
        data_count = sum(1 for skill in skills if any(kw in skill.lower() for kw in data_keywords))
        design_count = sum(1 for skill in skills if any(kw in skill.lower() for kw in design_keywords))
        
        # Determine category based on highest count
        if tech_count > data_count and tech_count > design_count:
            category = "Software Engineering"
        elif data_count > tech_count and data_count > design_count:
            category = "Data Science"
        elif design_count > tech_count and design_count > data_count:
            category = "Design"
        
        # Generate a simple summary
        latest_role = ""
        if experience:
            latest_role = experience[0].get("title", "Professional")
        
        highest_education = "degree"
        if education:
            highest_education = education[0].get("degree", "degree")
        
        summary = f"{experience_level} {latest_role or category} professional with {total_years} years of experience and a {highest_education}."
        
        # Generate key skills (top 5)
        key_skills = skills[:5] if skills else ["Communication", "Problem Solving", "Teamwork", "Organization", "Attention to Detail"]
        
        # Generate match keywords
        match_keywords = skills[:10] if skills else ["Professional", "Experienced", "Skilled", "Knowledgeable", "Proficient"]
        
        return {
            "summary": summary,
            "category": category,
            "key_skills": key_skills,
            "experience_level": experience_level,
            "match_keywords": match_keywords,
            "total_experience_years": total_years
        }
