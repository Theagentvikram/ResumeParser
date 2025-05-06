#!/usr/bin/env python3
"""
PDF Extraction Service for Smart Resume Selector
Uses regex-based extraction to pull structured information from resumes
"""
import os
import re
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

import fitz  # PyMuPDF

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pdf-extractor")

class PDFExtractor:
    """
    Extracts structured information from resume PDFs using regex patterns
    This extracts only the relevant fields to be passed to the LLM for summarization
    """
    
    def __init__(self):
        # Initialize common regex patterns
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.phone_pattern = r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
        
        # Common section headers in resumes
        self.section_headers = {
            'education': [r'education', r'academic background', r'qualifications', r'degrees'],
            'experience': [r'experience', r'employment', r'work history', r'professional experience'],
            'skills': [r'skills', r'technical skills', r'competencies', r'expertise'],
            'projects': [r'projects', r'portfolio', r'key projects'],
            'certifications': [r'certifications', r'certificates', r'licenses'],
            'languages': [r'languages', r'language proficiency'],
            'summary': [r'summary', r'profile', r'objective', r'professional summary']
        }
        
        # Common technical skills to look for
        self.tech_skills = [
            "python", "javascript", "typescript", "java", "c++", "c#", "ruby", "php", "swift", "kotlin", "go",
            "react", "angular", "vue", "node.js", "express", "django", "flask", "spring", "asp.net",
            "html", "css", "sass", "less", "bootstrap", "tailwind", "material-ui", "jquery",
            "sql", "nosql", "mongodb", "mysql", "postgresql", "oracle", "firebase", "redis", "elasticsearch",
            "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git", "github", "gitlab", "bitbucket",
            "rest", "graphql", "grpc", "microservices", "serverless", "ci/cd", "devops", "mlops",
            "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn",
            "machine learning", "deep learning", "natural language processing", "computer vision", "data science",
            "agile", "scrum", "kanban", "jira", "confluence", "trello", "asana"
        ]
        
        # Common soft skills to look for
        self.soft_skills = [
            "leadership", "management", "communication", "teamwork", "problem-solving", "critical thinking",
            "creativity", "time management", "organization", "adaptability", "flexibility", "resilience",
            "emotional intelligence", "conflict resolution", "negotiation", "presentation", "public speaking",
            "customer service", "client relations", "mentoring", "coaching", "collaboration", "attention to detail"
        ]
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from a PDF file"""
        try:
            logger.info(f"Extracting text from PDF: {file_path}")
            
            # Open the PDF
            try:
                doc = fitz.open(file_path)
            except Exception as e:
                logger.error(f"Error opening PDF: {str(e)}")
                # Try alternative approach with pdfplumber if available
                try:
                    import pdfplumber
                    with pdfplumber.open(file_path) as pdf:
                        text = ""
                        # Limit to first 5 pages for speed
                        for i in range(min(5, len(pdf.pages))):
                            text += pdf.pages[i].extract_text() or ""
                    return text
                except ImportError:
                    # If pdfplumber is not available, return empty string
                    logger.warning("pdfplumber not available for fallback PDF extraction")
                    return "Unable to extract text from PDF"
            
            # Extract text from each page (limit to first 5 pages for speed)
            text = ""
            try:
                for page_num in range(min(5, len(doc))):
                    try:
                        page = doc.load_page(page_num)
                        page_text = page.get_text()
                        text += page_text
                    except Exception as page_error:
                        logger.warning(f"Error extracting text from page {page_num}: {str(page_error)}")
                        continue
            except Exception as e:
                logger.error(f"Error iterating through PDF pages: {str(e)}")
            
            # Close the document
            try:
                doc.close()
            except:
                pass
            
            # If we couldn't extract any text, return a message
            if not text.strip():
                logger.warning("No text extracted from PDF")
                return "No text could be extracted from this PDF. Please try a different file."
            
            logger.info(f"Extracted {len(text)} characters from PDF")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return "Error extracting text from PDF. Please try a different file."
    
    def extract_name(self, text: str) -> str:
        """Extract name from resume text using regex"""
        lines = text.split('\n')
        # Assume the name is in the first few lines
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 40 and not any(keyword in line.lower() for keyword in ['resume', 'cv', 'curriculum', 'vitae', 'address', 'phone', 'email']):
                return line
        return "Unknown"
    
    def extract_email(self, text: str) -> str:
        """Extract email from resume text using regex"""
        emails = re.findall(self.email_pattern, text)
        return emails[0] if emails else "Unknown"
    
    def extract_phone(self, text: str) -> str:
        """Extract phone number from resume text using regex"""
        phones = re.findall(self.phone_pattern, text)
        return phones[0] if phones else "Unknown"
    
    def extract_skills(self, text: str) -> List[str]:
        """Extract skills from resume text using regex"""
        text = text.lower()
        
        # Find skills in text
        found_skills = []
        all_skills = self.tech_skills + self.soft_skills
        
        for skill in all_skills:
            if skill in text:
                # Make sure it's a whole word match
                pattern = r'\b' + re.escape(skill) + r'\b'
                if re.search(pattern, text):
                    found_skills.append(skill.title())  # Capitalize skill names
        
        # If no skills found, return some generic ones
        if not found_skills:
            return ["Communication", "Problem Solving", "Teamwork"]
        
        return sorted(list(set(found_skills)))[:15]  # Limit to 15 unique skills
    
    def extract_education(self, text: str) -> List[Dict[str, str]]:
        """Extract education details from resume text"""
        text = text.lower()
        education_section = self._extract_section(text, 'education')
        
        if not education_section:
            # Try to find education-related keywords in the entire text
            education_degrees = []
            degree_patterns = {
                "PhD": [r'ph\.?d\.?', r'doctor of philosophy', r'doctorate'],
                "Master's": [r'master', r'm\.s\.', r'm\.a\.', r'mba', r'msc'],
                "Bachelor's": [r'bachelor', r'b\.s\.', r'b\.a\.', r'bsc', r'undergraduate'],
                "Associate's": [r'associate', r'a\.s\.', r'a\.a\.'],
                "High School": [r'high school', r'secondary', r'hs diploma']
            }
            
            for degree, patterns in degree_patterns.items():
                for pattern in patterns:
                    if re.search(r'\b' + pattern + r'\b', text):
                        # Try to find the university near the degree mention
                        university_pattern = r'(?:' + re.escape(pattern) + r'.*?(?:university|college|institute|school)|(?:university|college|institute|school).*?' + re.escape(pattern) + r')'
                        university_match = re.search(university_pattern, text, re.IGNORECASE)
                        university = "Unknown University"
                        if university_match:
                            university_text = university_match.group(0)
                            # Extract university name
                            uni_names = re.findall(r'(?:University|College|Institute|School) of [A-Z][a-z]+|[A-Z][a-z]+ (?:University|College|Institute|School)', university_text)
                            if uni_names:
                                university = uni_names[0]
                        
                        # Try to find graduation year
                        year_pattern = r'\b(19|20)\d{2}\b'
                        years = re.findall(year_pattern, text)
                        graduation_year = max(map(int, years)) if years else None
                        
                        education_degrees.append({
                            "degree": degree,
                            "institution": university,
                            "year": graduation_year
                        })
                        break
            
            return education_degrees if education_degrees else [{"degree": "Bachelor's", "institution": "Unknown University", "year": None}]
        
        # Parse the education section
        education_entries = []
        lines = education_section.split('\n')
        current_entry = {"degree": "", "institution": "", "year": None}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check for degree
            for degree, patterns in degree_patterns.items():
                if any(re.search(r'\b' + pattern + r'\b', line, re.IGNORECASE) for pattern in patterns):
                    if current_entry["degree"]:  # Save previous entry
                        education_entries.append(current_entry.copy())
                    current_entry = {"degree": degree, "institution": "", "year": None}
                    break
            
            # Check for university/institution
            uni_pattern = r'(?:University|College|Institute|School) of [A-Z][a-z]+|[A-Z][a-z]+ (?:University|College|Institute|School)'
            uni_matches = re.findall(uni_pattern, line, re.IGNORECASE)
            if uni_matches:
                current_entry["institution"] = uni_matches[0]
            
            # Check for year
            year_pattern = r'\b(19|20)\d{2}\b'
            years = re.findall(year_pattern, line)
            if years:
                current_entry["year"] = max(map(int, years))
        
        # Add the last entry if it has a degree
        if current_entry["degree"]:
            education_entries.append(current_entry)
        
        return education_entries if education_entries else [{"degree": "Bachelor's", "institution": "Unknown University", "year": None}]
    
    def extract_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience details from resume text"""
        text = text.lower()
        experience_section = self._extract_section(text, 'experience')
        
        if not experience_section:
            # Try to find experience-related keywords in the entire text
            return self._estimate_experience_from_text(text)
        
        # Parse the experience section
        experience_entries = []
        
        # Look for job titles, companies, and dates
        job_pattern = r'(?:^|\n)([A-Z][A-Za-z\s]+)(?:,|\sat\s|\s-\s)([A-Za-z\s]+)(?:,|\s)(?:.*?)(\b(?:19|20)\d{2}\b(?:\s*[-–—]\s*(?:(?:19|20)\d{2}|Present|Current|Now))?)'
        job_matches = re.finditer(job_pattern, experience_section, re.MULTILINE)
        
        for match in job_matches:
            title, company, date_range = match.groups()
            
            # Parse date range
            start_year, end_year = self._parse_date_range(date_range)
            
            # Calculate duration
            duration = None
            if start_year and end_year:
                duration = end_year - start_year
            
            experience_entries.append({
                "title": title.strip(),
                "company": company.strip(),
                "start_year": start_year,
                "end_year": end_year,
                "duration": duration
            })
        
        return experience_entries if experience_entries else self._estimate_experience_from_text(text)
    
    def _estimate_experience_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Estimate experience from the entire text if no structured experience section found"""
        # Look for years of experience mentions
        exp_patterns = [
            r'(\d+)(?:\+)?\s*(?:years|yrs)(?:\s*of)?\s*experience',
            r'experience\s*(?:of|:)?\s*(\d+)(?:\+)?\s*(?:years|yrs)',
            r'(?:over|more than)\s*(\d+)\s*(?:years|yrs)(?:\s*of)?\s*experience'
        ]
        
        for pattern in exp_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                years = max(map(int, matches))
                current_year = 2025  # Using the current year from the metadata
                return [{
                    "title": "Professional",
                    "company": "Unknown",
                    "start_year": current_year - years,
                    "end_year": current_year,
                    "duration": years
                }]
        
        # Look for job titles and companies
        job_pattern = r'(?:^|\n)([A-Z][A-Za-z\s]+)(?:,|\sat\s|\s-\s)([A-Za-z\s]+)(?:,|\s)(?:.*?)(\b(?:19|20)\d{2}\b(?:\s*[-–—]\s*(?:(?:19|20)\d{2}|Present|Current|Now))?)'
        job_matches = re.finditer(job_pattern, text, re.MULTILINE)
        
        experience_entries = []
        for match in job_matches:
            title, company, date_range = match.groups()
            
            # Parse date range
            start_year, end_year = self._parse_date_range(date_range)
            
            # Calculate duration
            duration = None
            if start_year and end_year:
                duration = end_year - start_year
            
            experience_entries.append({
                "title": title.strip(),
                "company": company.strip(),
                "start_year": start_year,
                "end_year": end_year,
                "duration": duration
            })
        
        return experience_entries if experience_entries else [{
            "title": "Professional",
            "company": "Unknown",
            "start_year": None,
            "end_year": None,
            "duration": 0
        }]
    
    def _parse_date_range(self, date_range: str) -> tuple:
        """Parse a date range string into start and end years"""
        years = re.findall(r'\b(19|20)\d{2}\b', date_range)
        
        if not years:
            return None, None
        
        start_year = int(years[0])
        
        # Check if "Present" or similar is in the date range
        if re.search(r'Present|Current|Now', date_range, re.IGNORECASE):
            end_year = 2025  # Using the current year from the metadata
        elif len(years) > 1:
            end_year = int(years[1])
        else:
            end_year = start_year  # Default to same year if only one year found
        
        return start_year, end_year
    
    def extract_projects(self, text: str) -> List[Dict[str, str]]:
        """Extract project details from resume text"""
        text = text.lower()
        projects_section = self._extract_section(text, 'projects')
        
        if not projects_section:
            return []
        
        # Parse the projects section
        projects = []
        
        # Split by project (assuming each project starts with a title on a new line)
        project_pattern = r'(?:^|\n)([A-Z][A-Za-z0-9\s]+)(?::|-)(.+?)(?=\n[A-Z]|\Z)'
        project_matches = re.finditer(project_pattern, projects_section, re.MULTILINE | re.DOTALL)
        
        for match in project_matches:
            title, description = match.groups()
            projects.append({
                "title": title.strip(),
                "description": description.strip()
            })
        
        return projects
    
    def extract_total_experience_years(self, text: str) -> int:
        """Extract total years of experience from resume text"""
        text = text.lower()
        
        # First, try to find explicit mentions of years of experience
        exp_patterns = [
            r'(\d+)(?:\+)?\s*(?:years|yrs)(?:\s*of)?\s*experience',
            r'experience\s*(?:of|:)?\s*(\d+)(?:\+)?\s*(?:years|yrs)',
            r'(?:over|more than)\s*(\d+)\s*(?:years|yrs)(?:\s*of)?\s*experience'
        ]
        
        for pattern in exp_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return max(map(int, matches))
        
        # If no explicit mention, calculate from work experience
        experience_entries = self.extract_experience(text)
        
        if not experience_entries:
            return 0
        
        total_years = 0
        for entry in experience_entries:
            if entry.get("duration") is not None:
                total_years += entry["duration"]
        
        return total_years if total_years > 0 else 2  # Default to 2 years if calculation fails
    
    def _extract_section(self, text: str, section_name: str) -> Optional[str]:
        """Extract a specific section from the resume text"""
        # Get patterns for the requested section
        section_patterns = self.section_headers.get(section_name, [])
        if not section_patterns:
            return None
        
        # Create regex pattern to find the section
        section_pattern = '|'.join(section_patterns)
        section_regex = fr'(?:^|\n)(?:{section_pattern})(?::|\.|\n)(.*?)(?=\n(?:{"|".join([p for k, patterns in self.section_headers.items() for p in patterns if k != section_name])})|$)'
        
        # Search for the section
        match = re.search(section_regex, text, re.IGNORECASE | re.DOTALL)
        if not match:
            return None
        
        return match.group(1).strip()
    
    def extract_structured_data(self, file_path: str) -> Dict[str, Any]:
        """
        Extract structured data from a resume PDF
        This is the main method that combines all extraction functions
        """
        # Extract text from PDF
        text = self.extract_text_from_pdf(file_path)
        
        if "Error" in text or "Unable" in text:
            return {
                "error": text
            }
        
        # Extract structured data
        structured_data = {
            "name": self.extract_name(text),
            "email": self.extract_email(text),
            "phone": self.extract_phone(text),
            "skills": self.extract_skills(text),
            "education": self.extract_education(text),
            "experience": self.extract_experience(text),
            "projects": self.extract_projects(text),
            "total_experience_years": self.extract_total_experience_years(text),
            "raw_text": text[:1000]  # Include first 1000 chars of raw text for reference
        }
        
        return structured_data
