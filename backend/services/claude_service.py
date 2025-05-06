import re
import json
import random
from typing import Dict, List, Any
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_resume_with_regex(resume_text: str) -> Dict[str, Any]:
    """
    Analyze a resume using regex pattern matching to extract key information.
    This is a fallback method when AI models are not available.
    
    Args:
        resume_text: The text content of the resume
        
    Returns:
        Dictionary containing extracted information
    """
    # Log a sample of the text for debugging
    logger.info(f"Analyzing resume with regex. Text sample (first 200 chars): {resume_text[:200].replace(chr(10), ' ')}")
    
    # Normalize text for better pattern matching
    normalized_text = resume_text.lower()
    
    # Clean the text - remove extra whitespace
    cleaned_text = re.sub(r'\s+', ' ', resume_text).strip()
    
    # Extract information using pattern matching
    skills = extract_skills(normalized_text, resume_text)
    experience_years = extract_experience(normalized_text, resume_text)
    education_level = extract_education_level(normalized_text, resume_text)
    job_category = determine_job_category(normalized_text, resume_text)
    
    # Generate a summary
    summary = generate_summary(resume_text, skills, experience_years, education_level, job_category)
    
    # Log the extracted information
    logger.info(f"Regex analysis results: {len(skills)} skills, {experience_years} years experience, {education_level} education, {job_category} category")
    
    # Return the results
    return {
        "summary": summary,
        "skills": skills,
        "experience": experience_years,
        "educationLevel": education_level,
        "category": job_category
    }

def normalize_text(text: str) -> str:
    """Normalize text for better analysis"""
    # Convert to lowercase
    text = text.lower()
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Replace newlines with spaces
    text = text.replace('\n', ' ')
    
    # Remove special characters that might interfere with regex
    text = re.sub(r'[^\w\s\.]', ' ', text)
    
    return text

def extract_experience(normalized_text: str, original_text: str) -> int:
    """
    Extract years of experience from resume text
    """
    # Pattern for direct mention of years of experience
    direct_patterns = [
        r'(\d+)\+?\s+years?(?:\s+of)?\s+experience',
        r'experience\s+(?:of\s+)?(\d+)\+?\s+years?',
        r'(?:over|more\s+than)\s+(\d+)\s+years?(?:\s+of)?\s+experience',
        r'(\d+)\s*\+\s*years?(?:\s+of)?\s+(?:industry|professional|work)',
    ]
    
    for pattern in direct_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            # Direct mention found
            return int(match.group(1))
    
    # Try to calculate experience from job history
    job_dates = []
    
    # Pattern to find date ranges in work history
    date_patterns = [
        # Mon Year - Mon Year or Present format
        r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{4})\s*(?:–|-|to)\s*(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+(\d{4})|present|current)',
        # Year - Year or Present format
        r'(\d{4})\s*(?:–|-|to)\s*(?:(\d{4})|present|current)',
    ]
    
    for pattern in date_patterns:
        matches = re.finditer(pattern, normalized_text, re.IGNORECASE)
        for match in matches:
            if match.group(2) and match.group(2).isdigit():
                # Both years are specified
                start_year = int(match.group(1))
                end_year = int(match.group(2))
                job_dates.append((start_year, end_year))
            else:
                # End date is "present" or similar
                start_year = int(match.group(1))
                current_year = datetime.now().year
                job_dates.append((start_year, current_year))
    
    # Calculate total experience
    if job_dates:
        # Sort by start date
        job_dates.sort()
        total_exp = 0
        current_span = None
        
        for start_year, end_year in job_dates:
            # Validate the date range
            if end_year < start_year:
                continue
                
            # If first job or no overlap with previous
            if current_span is None:
                current_span = (start_year, end_year)
                total_exp += end_year - start_year
            # Check for overlap
            elif start_year <= current_span[1]:
                # Extend current span if needed
                if end_year > current_span[1]:
                    total_exp += end_year - current_span[1]
                    current_span = (current_span[0], end_year)
            # No overlap, new span
            else:
                current_span = (start_year, end_year)
                total_exp += end_year - start_year
        
        # Return calculated experience
        return max(total_exp, 1)
    
    # Fallback: Check graduation date if present
    grad_patterns = [
        r'graduated\s+(?:in|on)?\s*(\d{4})',
        r'class\s+of\s+(\d{4})',
        r'(?:degree|diploma|certificate)\s+(?:received|awarded|conferred)\s+(?:in|on)?\s*(\d{4})'
    ]
    
    for pattern in grad_patterns:
        match = re.search(pattern, normalized_text)
        if match:
            grad_year = int(match.group(1))
            current_year = datetime.now().year
            # Check if graduation year is reasonable
            if 1980 <= grad_year <= current_year:
                return max(current_year - grad_year, 0)
    
    # Final fallback: Make an educated guess based on content volume and structure
    line_count = len(normalized_text.split('\n'))
    word_count = len(normalized_text.split())
    
    if line_count > 70 or word_count > 700:
        return 5  # Larger resume suggests more experience
    elif line_count > 50 or word_count > 500:
        return 3  # Medium-sized resume
    else:
        return 1  # Shorter resume suggests less experience

def extract_education_level(normalized_text: str, original_text: str) -> str:
    """
    Determine the highest level of education from resume text
    """
    # Define education levels and their keywords patterns
    education_patterns = {
        "PhD": r'\b(?:ph\.?d\.?|doctor\s+of\s+philosophy|doctoral)\b',
        "Master's": r'\b(?:master\'?s?|ms\.?|m\.s\.?|m\.a\.?|mba|m\.b\.a\.?)\b',
        "Bachelor's": r'\b(?:bachelor\'?s?|ba|b\.a\.?|bs|b\.s\.?|b\.e\.?|btech|b\.tech\.?)\b',
        "Associate's": r'\b(?:associate\'?s?|a\.a\.?|a\.s\.?|a\.a\.s\.?)\b',
        "High School": r'\b(?:high\s+school|secondary\s+school|diploma|g\.?e\.?d\.?)\b'
    }
    
    # Check for each education level in order of highest to lowest
    for level, pattern in education_patterns.items():
        if re.search(pattern, normalized_text, re.IGNORECASE):
            return level
    
    # If no education level is explicitly mentioned but college names are present
    college_patterns = [
        r'\b(?:university|college|institute|school)\s+of\b',
        r'\b(?:university|college|institute)\b'
    ]
    
    for pattern in college_patterns:
        if re.search(pattern, normalized_text, re.IGNORECASE):
            # Found a college reference but no specific degree
            # Default to Bachelor's as most common
            return "Bachelor's"
    
    # Default if no education information found
    return "High School"

def extract_skills(normalized_text: str, original_text: str) -> List[str]:
    """
    Extract skills from resume text using pattern matching and common skill lists
    """
    # Comprehensive list of common technical and soft skills
    common_tech_skills = [
        # Programming Languages
        "python", "java", "javascript", "typescript", "c\\+\\+", "c#", "ruby", "php", "swift", "kotlin", "go", "rust",
        "scala", "perl", "r", "matlab", "bash", "shell", "sql", "html", "css", "sass", "less",
        
        # Frameworks & Libraries
        "react", "angular", "vue", "django", "flask", "spring", "asp\\.net", "node\\.js", "express\\.js", 
        "jquery", "bootstrap", "tailwind", "laravel", "symfony", "rails", "pytorch", "tensorflow",
        "keras", "scikit-learn", "pandas", "numpy", "matplotlib", "seaborn", 
        
        # Cloud & DevOps
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "terraform", "jenkins", "github actions",
        "circleci", "travis", "ansible", "chef", "puppet", "serverless", "lambda", "s3", "ec2", "rds",
        
        # Databases
        "mysql", "postgresql", "mongodb", "sqlite", "oracle", "sql server", "dynamodb", "cassandra", "redis",
        "elasticsearch", "firebase", "neo4j",
        
        # Tools & Methodologies
        "git", "github", "gitlab", "bitbucket", "jira", "confluence", "agile", "scrum", "kanban", "tdd", "ci/cd",
        "rest", "graphql", "soap", "microservices", "mvc", "oop", "functional programming",
        
        # Data Science & AI
        "machine learning", "deep learning", "artificial intelligence", "nlp", "computer vision", "data mining",
        "data analysis", "data visualization", "statistical analysis", "a/b testing", "big data", "hadoop", "spark",
        
        # Design & UX
        "figma", "sketch", "adobe xd", "photoshop", "illustrator", "ui design", "ux design", "wireframing",
        "prototyping", "responsive design", "accessibility", "user research",
        
        # Soft Skills
        "leadership", "communication", "teamwork", "problem solving", "critical thinking", "time management",
        "project management", "customer service", "presentation", "negotiation", "conflict resolution"
    ]
    
    # Extract skills by finding matches with word boundaries
    found_skills = set()
    for skill in common_tech_skills:
        # Use word boundary for more precise matching
        pattern = r'\b' + skill + r'\b'
        if re.search(pattern, normalized_text, re.IGNORECASE):
            # Use the original capitalization if possible by searching in the original text
            original_match = re.search(pattern, original_text, re.IGNORECASE)
            if original_match:
                found_skills.add(original_match.group(0))
            else:
                # Format multi-word skills with proper capitalization
                found_skills.add(' '.join(word.capitalize() if word.lower() not in ('and', 'of', 'the', 'for', 'with') 
                                        else word.lower() for word in skill.split()))
    
    # Look for skill-specific sections in the resume
    skill_sections = []
    skill_section_patterns = [
        r'(?:technical|core|key|professional)\s+skills?[\s\:]+(.+?)(?:\n\n|\n[A-Z])',
        r'skills(?:\s+&|\s+and)?\s+(?:expertise|proficiencies)[\s\:]+(.+?)(?:\n\n|\n[A-Z])',
        r'(?:technical|professional|areas\s+of)\s+expertise[\s\:]+(.+?)(?:\n\n|\n[A-Z])'
    ]
    
    for pattern in skill_section_patterns:
        skill_section_match = re.search(pattern, normalized_text, re.IGNORECASE | re.DOTALL)
        if skill_section_match:
            skill_sections.append(skill_section_match.group(1))
    
    # Extract skills from skill sections
    if skill_sections:
        for section in skill_sections:
            # Split by common separators in skill lists
            items = re.split(r'[,•|;]|\s+and\s+|\n-\s+|\n•\s+', section)
            for item in items:
                item = item.strip()
                if len(item) > 2 and len(item) < 30:  # Reasonable skill name length
                    found_skills.add(item.strip())
    
    # Check for certifications
    cert_pattern = r'\b(?:certified|certification|certificate)\s+(?:in|as|on)?\s+([A-Za-z0-9\s\-]+)'
    cert_matches = re.finditer(cert_pattern, normalized_text, re.IGNORECASE)
    for match in cert_matches:
        cert = match.group(1).strip()
        if len(cert) > 2 and len(cert) < 50:  # Reasonable certification name length
            found_skills.add(f"{cert} Certification")
    
    # Convert set to list, filter out too short or too long entries and limit to 15 most relevant
    skills_list = [skill for skill in found_skills if 2 < len(skill) < 30]
    
    # Ensure we have at least some skills even if none were found
    if not skills_list:
        # Look for capitalized words that might be technologies or tools
        capitalized_words = re.findall(r'\b[A-Z][a-zA-Z]+\b', original_text)
        for word in capitalized_words:
            if len(word) > 2 and word not in ('I', 'A', 'The', 'In', 'And', 'For'):
                skills_list.append(word)
    
    # Limit to top 15 skills to avoid overwhelming results
    return sorted(list(skills_list))[:15]

def determine_job_category(normalized_text: str, original_text: str) -> str:
    """
    Determine the most likely job category based on resume content
    """
    # Define job categories and their associated keywords
    categories = {
        "Software Engineering": ["software engineer", "developer", "programmer", "coding", "java", "python", "c#", 
                               "javascript", "react", "angular", "vue", "web development", "frontend", "backend",
                               "full stack", "mobile app", "android", "ios", "api", "agile", "scrum", "devops"],
                               
        "Data Science": ["data scientist", "machine learning", "ml", "ai", "artificial intelligence", "deep learning",
                        "statistics", "statistical analysis", "r", "python", "pandas", "numpy", "tensorflow",
                        "pytorch", "data mining", "data analysis", "big data", "data visualization", "model"],
                        
        "Data Engineering": ["data engineer", "data pipeline", "etl", "hadoop", "spark", "kafka", "data warehouse",
                           "data modeling", "sql", "database", "nosql", "data infrastructure", "airflow"],
                           
        "Project Management": ["project manager", "product manager", "program manager", "agile", "scrum", "kanban",
                             "waterfall", "pmp", "prince2", "stakeholder", "requirement", "roadmap", "timeline",
                             "project plan", "risk management", "delivery", "milestone"],
                             
        "Marketing": ["marketing", "seo", "sem", "digital marketing", "content marketing", "social media",
                    "campaign", "analytics", "advertising", "market research", "brand", "content strategy",
                    "google analytics", "conversion rate", "growth hacking", "customer acquisition"],
                    
        "Sales": ["sales", "account executive", "business development", "customer acquisition", "lead generation",
                 "sales funnel", "crm", "salesforce", "negotiation", "cold calling", "relationship building",
                 "revenue", "quota", "client relationship", "closing deals"],
                 
        "Customer Support": ["customer support", "customer service", "technical support", "help desk", "client success",
                           "service desk", "ticketing system", "zendesk", "customer satisfaction", "issue resolution"],
                           
        "Design": ["designer", "graphic design", "ui", "ux", "user interface", "user experience", "visual design",
                  "figma", "sketch", "adobe", "photoshop", "illustrator", "indesign", "typography", "web design"],
                  
        "Human Resources": ["hr", "human resources", "recruitment", "talent acquisition", "onboarding", "employee relations",
                          "training", "development", "compensation", "benefits", "hr policy", "performance management"],
                          
        "Finance": ["finance", "accounting", "financial analysis", "budget", "forecast", "audit", "tax", "cpa", "cfa",
                  "bookkeeping", "accounts payable", "accounts receivable", "financial statement", "balance sheet"]
    }
    
    # Count occurrences of keywords for each category
    category_scores = {category: 0 for category in categories}
    
    for category, keywords in categories.items():
        for keyword in keywords:
            # Count occurrences of the keyword surrounded by word boundaries
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', normalized_text, re.IGNORECASE))
            category_scores[category] += count
    
    # Find the category with the highest score
    max_score = 0
    best_category = "Professional"  # Default
    
    for category, score in category_scores.items():
        if score > max_score:
            max_score = score
            best_category = category
    
    # If no strong signal was found, try to extract job titles
    if max_score < 3:
        # Common job title patterns
        job_title_patterns = [
            r'(?:^|\n)(?:professional\s+)?(?:experience|title|position)[:\s]+([A-Za-z\s\,\-\&]+)(?:\n|$)',
            r'(?:^|\n)([A-Z][A-Za-z\s\-]+)(?:\n|$)'  # Look for capitalized lines that might be job titles
        ]
        
        job_titles = []
        for pattern in job_title_patterns:
            matches = re.finditer(pattern, original_text)
            for match in matches:
                title = match.group(1).strip()
                if 3 < len(title) < 40:  # Reasonable title length
                    job_titles.append(title.lower())
        
        # Now check which category best matches these job titles
        for title in job_titles:
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword in title:
                        category_scores[category] += 2
        
        # Recheck for best category
        for category, score in category_scores.items():
            if score > max_score:
                max_score = score
                best_category = category
    
    return best_category

def generate_summary(resume_text: str, skills: List[str], experience_years: int, education_level: str, job_category: str) -> str:
    """
    Generate a professional summary based on extracted information
    """
    # Try to extract the candidate's name
    name = "Professional"
    name_patterns = [
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})$',  # Common format at start of resume
        r'(?:name|contact)[\s\:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})'  # After "Name:" or "Contact:"
    ]
    
    for pattern in name_patterns:
        name_matches = re.finditer(pattern, resume_text, re.MULTILINE)
        for match in name_matches:
            potential_name = match.group(1).strip()
            # Check if it's a reasonable name (not too long or short)
            if 4 < len(potential_name) < 40:
                name = potential_name.split()[0]  # Just use first name
                break
    
    # Try to extract their most recent role
    recent_role = job_category + " professional"
    role_patterns = [
        r'(?:current|present|latest|recent)\s+(?:position|role|title)[:\s]+([A-Za-z\s\,\-\&]+)',
        r'(?:^|\n)([A-Z][A-Za-z\s\-]+)(?:\n|$)'  # Look for capitalized lines that might be job titles
    ]
    
    for pattern in role_patterns:
        role_matches = re.finditer(pattern, resume_text, re.IGNORECASE)
        for match in role_matches:
            potential_role = match.group(1).strip()
            if 3 < len(potential_role) < 40:  # Reasonable title length
                recent_role = potential_role
                break
    
    # Generate experience level description
    experience_description = ""
    if experience_years < 1:
        experience_description = "an entry-level"
    elif experience_years < 3:
        experience_description = "a junior"
    elif experience_years < 6:
        experience_description = "a mid-level"
    elif experience_years < 10:
        experience_description = "a senior"
    else:
        experience_description = "an experienced"
    
    # Get top skills (up to 5)
    top_skills = skills[:min(5, len(skills))]
    skills_text = ", ".join(top_skills)
    
    # Generate the summary
    if len(top_skills) > 0:
        summary = f"{name} is {experience_description} {job_category} professional with {experience_years} years of experience. "
        summary += f"Their background includes {recent_role} roles where they've applied skills in {skills_text}. "
        summary += f"They hold {education_level} level education and demonstrate strong expertise in their field."
    else:
        summary = f"{name} is {experience_description} {job_category} professional with {experience_years} years of experience. "
        summary += f"Their background includes {recent_role} roles focusing on their area of expertise. "
        summary += f"They hold {education_level} level education and are qualified for positions in this field."
    
    return summary
