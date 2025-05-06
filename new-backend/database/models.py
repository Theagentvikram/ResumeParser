"""
Database models for the ResuMatch application
"""
from sqlalchemy import Column, Integer, String, Float, Text, create_engine, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
import json
from typing import List, Optional, Dict, Any
import datetime

# Create the base class for declarative models
Base = declarative_base()

# Define the association table for many-to-many relationship between Resume and Skill
resume_skills = Table(
    'resume_skills',
    Base.metadata,
    Column('resume_id', Integer, ForeignKey('resumes.id')),
    Column('skill_id', Integer, ForeignKey('skills.id'))
)

class Skill(Base):
    """Skill model for storing resume skills"""
    __tablename__ = 'skills'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    
    # Relationship to resumes
    resumes = relationship("Resume", secondary=resume_skills, back_populates="skills")
    
    def __repr__(self):
        return f"<Skill(name='{self.name}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name
        }

class Resume(Base):
    """Resume model for storing resume data"""
    __tablename__ = 'resumes'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    full_text = Column(Text, nullable=True)
    
    # Extracted information
    name = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    experience_years = Column(Float, nullable=True)
    education_level = Column(String(100), nullable=True)
    role = Column(String(100), nullable=True)
    
    # Vector embedding for similarity search
    embedding = Column(Text, nullable=True)  # Store as JSON string
    
    # Upload timestamp
    created_at = Column(String(50), default=lambda: datetime.datetime.now().isoformat())
    
    # Relationships
    skills = relationship("Skill", secondary=resume_skills, back_populates="resumes")
    
    def __repr__(self):
        return f"<Resume(name='{self.name}', role='{self.role}')>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "name": self.name,
            "summary": self.summary,
            "experience_years": self.experience_years,
            "education_level": self.education_level,
            "role": self.role,
            "skills": [skill.name for skill in self.skills],
            "created_at": self.created_at
        }
    
    def set_embedding(self, embedding_array):
        """Store the embedding as a JSON string"""
        self.embedding = json.dumps(embedding_array.tolist())
    
    def get_embedding(self):
        """Get the embedding as a numpy array"""
        import numpy as np
        if self.embedding:
            return np.array(json.loads(self.embedding))
        return None

def init_db(db_path="sqlite:///database/resumes.db"):
    """Initialize the database"""
    engine = create_engine(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

def get_db_session(db_path="sqlite:///database/resumes.db"):
    """Get a database session"""
    engine = create_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()
