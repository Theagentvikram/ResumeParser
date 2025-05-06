#!/usr/bin/env python3
"""
Database Service for Smart Resume Selector
Uses SQLite to store resume data and metadata
"""
import os
import json
import sqlite3
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("database-service")

class DatabaseService:
    """
    Service for storing and retrieving resume data in SQLite
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the database service
        
        Args:
            db_path: Path to SQLite database file
        """
        if db_path is None:
            # Use default path in db directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            db_dir = os.path.join(base_dir, "db")
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "resume.db")
        
        self.db_path = db_path
        self.conn = None
        
        # Initialize database
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize the SQLite database and create tables if they don't exist"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Create resumes table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS resumes (
                id TEXT PRIMARY KEY,
                name TEXT,
                email TEXT,
                phone TEXT,
                file_path TEXT,
                upload_date TEXT,
                raw_text TEXT
            )
            ''')
            
            # Create summaries table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS summaries (
                id TEXT PRIMARY KEY,
                resume_id TEXT,
                summary TEXT,
                category TEXT,
                experience_level TEXT,
                total_experience_years INTEGER,
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
            ''')
            
            # Create skills table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id TEXT,
                skill TEXT,
                is_key_skill INTEGER,
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
            ''')
            
            # Create education table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS education (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id TEXT,
                degree TEXT,
                institution TEXT,
                year INTEGER,
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
            ''')
            
            # Create experience table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS experience (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id TEXT,
                title TEXT,
                company TEXT,
                start_year INTEGER,
                end_year INTEGER,
                duration INTEGER,
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
            ''')
            
            # Create projects table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id TEXT,
                title TEXT,
                description TEXT,
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
            ''')
            
            # Create keywords table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id TEXT,
                keyword TEXT,
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
            ''')
            
            # Create embeddings table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS embeddings (
                resume_id TEXT PRIMARY KEY,
                embedding_json TEXT,
                FOREIGN KEY (resume_id) REFERENCES resumes (id)
            )
            ''')
            
            self.conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            if self.conn:
                self.conn.close()
                self.conn = None
    
    def _ensure_connection(self):
        """Ensure database connection is active"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path)
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def save_resume(self, resume_id: str, structured_data: Dict[str, Any], file_path: str) -> bool:
        """
        Save resume data to database
        
        Args:
            resume_id: Unique ID for the resume
            structured_data: Structured resume data from PDF extractor
            file_path: Path to the uploaded PDF file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Extract basic resume data
            name = structured_data.get("name", "Unknown")
            email = structured_data.get("email", "Unknown")
            phone = structured_data.get("phone", "Unknown")
            raw_text = structured_data.get("raw_text", "")
            upload_date = datetime.now().isoformat()
            
            # Insert into resumes table
            cursor.execute(
                "INSERT OR REPLACE INTO resumes (id, name, email, phone, file_path, upload_date, raw_text) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (resume_id, name, email, phone, file_path, upload_date, raw_text)
            )
            
            # Insert education data
            education_list = structured_data.get("education", [])
            for edu in education_list:
                degree = edu.get("degree", "")
                institution = edu.get("institution", "")
                year = edu.get("year")
                
                cursor.execute(
                    "INSERT INTO education (resume_id, degree, institution, year) VALUES (?, ?, ?, ?)",
                    (resume_id, degree, institution, year)
                )
            
            # Insert experience data
            experience_list = structured_data.get("experience", [])
            for exp in experience_list:
                title = exp.get("title", "")
                company = exp.get("company", "")
                start_year = exp.get("start_year")
                end_year = exp.get("end_year")
                duration = exp.get("duration")
                
                cursor.execute(
                    "INSERT INTO experience (resume_id, title, company, start_year, end_year, duration) VALUES (?, ?, ?, ?, ?, ?)",
                    (resume_id, title, company, start_year, end_year, duration)
                )
            
            # Insert skills data
            skills_list = structured_data.get("skills", [])
            for skill in skills_list:
                cursor.execute(
                    "INSERT INTO skills (resume_id, skill, is_key_skill) VALUES (?, ?, ?)",
                    (resume_id, skill, 0)  # Not a key skill by default
                )
            
            # Insert projects data
            projects_list = structured_data.get("projects", [])
            for proj in projects_list:
                title = proj.get("title", "")
                description = proj.get("description", "")
                
                cursor.execute(
                    "INSERT INTO projects (resume_id, title, description) VALUES (?, ?, ?)",
                    (resume_id, title, description)
                )
            
            self.conn.commit()
            logger.info(f"Saved resume data for ID: {resume_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving resume data: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def save_summary(self, resume_id: str, summary_data: Dict[str, Any], embedding: Any = None) -> bool:
        """
        Save resume summary and embedding to database
        
        Args:
            resume_id: Unique ID for the resume
            summary_data: Summary data from Mistral
            embedding: Optional embedding vector
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Extract summary data
            summary = summary_data.get("summary", "")
            category = summary_data.get("category", "")
            experience_level = summary_data.get("experience_level", "")
            total_experience_years = summary_data.get("total_experience_years", 0)
            
            # Insert into summaries table
            cursor.execute(
                "INSERT OR REPLACE INTO summaries (id, resume_id, summary, category, experience_level, total_experience_years) VALUES (?, ?, ?, ?, ?, ?)",
                (resume_id, resume_id, summary, category, experience_level, total_experience_years)
            )
            
            # Insert key skills
            key_skills = summary_data.get("key_skills", [])
            for skill in key_skills:
                # Check if skill already exists
                cursor.execute(
                    "SELECT id FROM skills WHERE resume_id = ? AND skill = ?",
                    (resume_id, skill)
                )
                result = cursor.fetchone()
                
                if result:
                    # Update existing skill to mark as key skill
                    cursor.execute(
                        "UPDATE skills SET is_key_skill = 1 WHERE resume_id = ? AND skill = ?",
                        (resume_id, skill)
                    )
                else:
                    # Insert new key skill
                    cursor.execute(
                        "INSERT INTO skills (resume_id, skill, is_key_skill) VALUES (?, ?, ?)",
                        (resume_id, skill, 1)
                    )
            
            # Insert match keywords
            match_keywords = summary_data.get("match_keywords", [])
            for keyword in match_keywords:
                cursor.execute(
                    "INSERT INTO keywords (resume_id, keyword) VALUES (?, ?)",
                    (resume_id, keyword)
                )
            
            # Insert embedding if provided
            if embedding is not None:
                embedding_json = json.dumps(embedding.tolist() if hasattr(embedding, 'tolist') else embedding)
                cursor.execute(
                    "INSERT OR REPLACE INTO embeddings (resume_id, embedding_json) VALUES (?, ?)",
                    (resume_id, embedding_json)
                )
            
            self.conn.commit()
            logger.info(f"Saved summary data for resume ID: {resume_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving summary data: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def get_resume(self, resume_id: str) -> Optional[Dict[str, Any]]:
        """
        Get resume data by ID
        
        Args:
            resume_id: Unique ID for the resume
            
        Returns:
            Dictionary with resume data or None if not found
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Get basic resume data
            cursor.execute(
                "SELECT id, name, email, phone, file_path, upload_date FROM resumes WHERE id = ?",
                (resume_id,)
            )
            resume_data = cursor.fetchone()
            
            if not resume_data:
                return None
            
            # Create resume dictionary
            resume = {
                "id": resume_data[0],
                "name": resume_data[1],
                "email": resume_data[2],
                "phone": resume_data[3],
                "file_path": resume_data[4],
                "upload_date": resume_data[5]
            }
            
            # Get summary data
            cursor.execute(
                "SELECT summary, category, experience_level, total_experience_years FROM summaries WHERE resume_id = ?",
                (resume_id,)
            )
            summary_data = cursor.fetchone()
            
            if summary_data:
                resume["summary"] = summary_data[0]
                resume["category"] = summary_data[1]
                resume["experience_level"] = summary_data[2]
                resume["total_experience_years"] = summary_data[3]
            
            # Get skills
            cursor.execute(
                "SELECT skill, is_key_skill FROM skills WHERE resume_id = ?",
                (resume_id,)
            )
            skills_data = cursor.fetchall()
            
            resume["skills"] = [skill[0] for skill in skills_data]
            resume["key_skills"] = [skill[0] for skill in skills_data if skill[1] == 1]
            
            # Get education
            cursor.execute(
                "SELECT degree, institution, year FROM education WHERE resume_id = ?",
                (resume_id,)
            )
            education_data = cursor.fetchall()
            
            resume["education"] = [
                {
                    "degree": edu[0],
                    "institution": edu[1],
                    "year": edu[2]
                }
                for edu in education_data
            ]
            
            # Get experience
            cursor.execute(
                "SELECT title, company, start_year, end_year, duration FROM experience WHERE resume_id = ?",
                (resume_id,)
            )
            experience_data = cursor.fetchall()
            
            resume["experience"] = [
                {
                    "title": exp[0],
                    "company": exp[1],
                    "start_year": exp[2],
                    "end_year": exp[3],
                    "duration": exp[4]
                }
                for exp in experience_data
            ]
            
            # Get projects
            cursor.execute(
                "SELECT title, description FROM projects WHERE resume_id = ?",
                (resume_id,)
            )
            projects_data = cursor.fetchall()
            
            resume["projects"] = [
                {
                    "title": proj[0],
                    "description": proj[1]
                }
                for proj in projects_data
            ]
            
            # Get keywords
            cursor.execute(
                "SELECT keyword FROM keywords WHERE resume_id = ?",
                (resume_id,)
            )
            keywords_data = cursor.fetchall()
            
            resume["match_keywords"] = [keyword[0] for keyword in keywords_data]
            
            # Get embedding
            cursor.execute(
                "SELECT embedding_json FROM embeddings WHERE resume_id = ?",
                (resume_id,)
            )
            embedding_data = cursor.fetchone()
            
            if embedding_data:
                resume["embedding"] = json.loads(embedding_data[0])
            
            return resume
        except Exception as e:
            logger.error(f"Error getting resume data: {str(e)}")
            return None
    
    def get_all_resumes(self) -> List[Dict[str, Any]]:
        """
        Get all resumes in the database
        
        Returns:
            List of dictionaries with resume data
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Get all resume IDs
            cursor.execute("SELECT id FROM resumes")
            resume_ids = cursor.fetchall()
            
            # Get data for each resume
            resumes = []
            for (resume_id,) in resume_ids:
                resume = self.get_resume(resume_id)
                if resume:
                    resumes.append(resume)
            
            return resumes
        except Exception as e:
            logger.error(f"Error getting all resumes: {str(e)}")
            return []
    
    def get_resume_summaries(self) -> List[Dict[str, Any]]:
        """
        Get summaries for all resumes
        
        Returns:
            List of dictionaries with resume summaries
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Get resume summaries
            cursor.execute("""
                SELECT r.id, r.name, s.summary, s.category, s.experience_level, s.total_experience_years
                FROM resumes r
                JOIN summaries s ON r.id = s.resume_id
            """)
            summary_data = cursor.fetchall()
            
            summaries = []
            for data in summary_data:
                resume_id = data[0]
                
                # Get key skills
                cursor.execute(
                    "SELECT skill FROM skills WHERE resume_id = ? AND is_key_skill = 1",
                    (resume_id,)
                )
                key_skills_data = cursor.fetchall()
                key_skills = [skill[0] for skill in key_skills_data]
                
                # Get match keywords
                cursor.execute(
                    "SELECT keyword FROM keywords WHERE resume_id = ?",
                    (resume_id,)
                )
                keywords_data = cursor.fetchall()
                match_keywords = [keyword[0] for keyword in keywords_data]
                
                # Get embedding
                cursor.execute(
                    "SELECT embedding_json FROM embeddings WHERE resume_id = ?",
                    (resume_id,)
                )
                embedding_data = cursor.fetchone()
                embedding = json.loads(embedding_data[0]) if embedding_data else None
                
                summaries.append({
                    "id": resume_id,
                    "name": data[1],
                    "summary": data[2],
                    "category": data[3],
                    "experience_level": data[4],
                    "total_experience_years": data[5],
                    "key_skills": key_skills,
                    "match_keywords": match_keywords,
                    "embedding": embedding
                })
            
            return summaries
        except Exception as e:
            logger.error(f"Error getting resume summaries: {str(e)}")
            return []
    
    def delete_resume(self, resume_id: str) -> bool:
        """
        Delete a resume and all associated data
        
        Args:
            resume_id: Unique ID for the resume
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Delete from all tables
            tables = ["skills", "education", "experience", "projects", "keywords", "embeddings", "summaries", "resumes"]
            for table in tables:
                cursor.execute(f"DELETE FROM {table} WHERE resume_id = ?", (resume_id,))
            
            self.conn.commit()
            logger.info(f"Deleted resume with ID: {resume_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting resume: {str(e)}")
            if self.conn:
                self.conn.rollback()
            return False
    
    def get_all_skills(self) -> List[str]:
        """
        Get all unique skills in the database
        
        Returns:
            List of unique skills
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT DISTINCT skill FROM skills")
            skills_data = cursor.fetchall()
            
            return [skill[0] for skill in skills_data]
        except Exception as e:
            logger.error(f"Error getting all skills: {str(e)}")
            return []
    
    def filter_resumes(self, filters: Dict[str, Any]) -> List[str]:
        """
        Filter resumes based on criteria
        
        Args:
            filters: Dictionary with filter criteria
            
        Returns:
            List of resume IDs matching the filters
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            query = "SELECT DISTINCT r.id FROM resumes r"
            params = []
            where_clauses = []
            
            # Add joins based on filters
            if filters.get("skills"):
                query += " JOIN skills sk ON r.id = sk.resume_id"
            if filters.get("category"):
                query += " JOIN summaries s ON r.id = s.resume_id"
            if filters.get("experience_years_min") or filters.get("experience_years_max"):
                if " JOIN summaries s ON r.id = s.resume_id" not in query:
                    query += " JOIN summaries s ON r.id = s.resume_id"
            
            # Add filter conditions
            if filters.get("skills"):
                skills = filters["skills"]
                if isinstance(skills, str):
                    skills = [skills]
                
                skill_placeholders = ", ".join(["?"] * len(skills))
                where_clauses.append(f"sk.skill IN ({skill_placeholders})")
                params.extend(skills)
            
            if filters.get("category"):
                where_clauses.append("s.category = ?")
                params.append(filters["category"])
            
            if filters.get("experience_years_min"):
                where_clauses.append("s.total_experience_years >= ?")
                params.append(filters["experience_years_min"])
            
            if filters.get("experience_years_max"):
                where_clauses.append("s.total_experience_years <= ?")
                params.append(filters["experience_years_max"])
            
            # Add WHERE clause if there are any conditions
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            cursor.execute(query, params)
            resume_ids = cursor.fetchall()
            
            return [resume_id[0] for resume_id in resume_ids]
        except Exception as e:
            logger.error(f"Error filtering resumes: {str(e)}")
            return []
