#!/usr/bin/env python3
"""
Embedding Service for Smart Resume Selector
Uses SentenceTransformers for creating embeddings for semantic search
"""
import os
import json
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Union

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("embedding-service")

class EmbeddingService:
    """
    Service for creating and comparing embeddings for resume summaries
    Uses SentenceTransformers for semantic search
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the embedding service
        
        Args:
            model_name: Name of the SentenceTransformers model to use
        """
        self.model_name = model_name
        self.model = None
        self.is_available = self._initialize_model()
        
        if not self.is_available:
            logger.warning("SentenceTransformers not available. Using fallback embedding method.")
        else:
            logger.info(f"Embedding service initialized with model: {model_name}")
    
    def _initialize_model(self) -> bool:
        """Initialize the SentenceTransformers model"""
        try:
            # Import SentenceTransformers (lazy import to avoid startup errors if not installed)
            from sentence_transformers import SentenceTransformer
            
            # Load the model
            self.model = SentenceTransformer(self.model_name)
            return True
        except ImportError:
            logger.warning("SentenceTransformers not installed. Please install with: pip install sentence-transformers")
            return False
        except Exception as e:
            logger.error(f"Error initializing SentenceTransformers model: {str(e)}")
            return False
    
    def get_embedding(self, text: str) -> Union[np.ndarray, List[float]]:
        """
        Get embedding for a text using SentenceTransformers
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array or list of floats (fallback)
        """
        if not self.is_available:
            return self._fallback_embedding(text)
        
        try:
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return self._fallback_embedding(text)
    
    def _fallback_embedding(self, text: str) -> List[float]:
        """
        Fallback method to generate a simple embedding without SentenceTransformers
        Uses word frequency and character-level features
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding
        """
        logger.info("Using fallback embedding method")
        
        # Normalize text
        text = text.lower()
        
        # Create a simple embedding based on character frequencies and text length
        char_freq = {}
        for char in text:
            if char.isalnum():
                char_freq[char] = char_freq.get(char, 0) + 1
        
        # Create a fixed-size embedding (100 dimensions)
        embedding = [0.0] * 100
        
        # Fill in character frequencies (first 36 dimensions for a-z and 0-9)
        for i, char in enumerate("abcdefghijklmnopqrstuvwxyz0123456789"):
            if i < 36:
                embedding[i] = char_freq.get(char, 0) / (len(text) + 1)
        
        # Add some text statistics (next 10 dimensions)
        embedding[36] = len(text) / 1000  # Normalized text length
        embedding[37] = len(text.split()) / 100  # Normalized word count
        embedding[38] = sum(1 for c in text if c.isupper()) / (len(text) + 1)  # Uppercase ratio
        embedding[39] = sum(1 for c in text if c.isdigit()) / (len(text) + 1)  # Digit ratio
        embedding[40] = sum(1 for c in text if c.isspace()) / (len(text) + 1)  # Space ratio
        embedding[41] = sum(1 for c in text if c in ".,;:!?") / (len(text) + 1)  # Punctuation ratio
        
        # Add word-based features (next 54 dimensions)
        common_words = [
            "experience", "skills", "education", "project", "work", "professional", "team", "development",
            "management", "data", "software", "design", "research", "analysis", "technical", "business",
            "communication", "leadership", "problem", "solution", "technology", "engineering", "science",
            "degree", "university", "college", "bachelor", "master", "phd", "certification", "training",
            "years", "month", "responsible", "lead", "develop", "implement", "create", "analyze", "design",
            "manage", "coordinate", "collaborate", "improve", "increase", "reduce", "support", "maintain",
            "test", "deploy", "build", "architect", "optimize", "innovate"
        ]
        
        for i, word in enumerate(common_words):
            if i + 42 < 100:  # Stay within 100 dimensions
                embedding[i + 42] = text.count(word) / (len(text.split()) + 1)
        
        return embedding
    
    def calculate_similarity(self, embedding1: Union[np.ndarray, List[float]], embedding2: Union[np.ndarray, List[float]]) -> float:
        """
        Calculate cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score (0-1)
        """
        try:
            # Convert to numpy arrays if they aren't already
            if not isinstance(embedding1, np.ndarray):
                embedding1 = np.array(embedding1)
            if not isinstance(embedding2, np.ndarray):
                embedding2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(embedding1, embedding2)
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            
            # Ensure the result is between 0 and 1
            similarity = max(0.0, min(1.0, similarity))
            
            return float(similarity)
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            return 0.0
    
    def rank_resumes(self, query: str, resume_summaries: List[Dict[str, Any]], top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Rank resumes based on similarity to a query
        
        Args:
            query: Recruiter's query text
            resume_summaries: List of resume summaries with embeddings
            top_n: Number of top matches to return
            
        Returns:
            List of top matching resumes with similarity scores
        """
        try:
            # Get embedding for the query
            query_embedding = self.get_embedding(query)
            
            # Calculate similarity for each resume
            results = []
            for resume in resume_summaries:
                # Get or calculate resume embedding
                resume_embedding = resume.get("embedding")
                if resume_embedding is None:
                    # Create embedding from summary and keywords
                    summary_text = resume.get("summary", "")
                    keywords = resume.get("match_keywords", [])
                    key_skills = resume.get("key_skills", [])
                    
                    embedding_text = summary_text
                    if keywords:
                        embedding_text += " " + " ".join(keywords)
                    if key_skills:
                        embedding_text += " " + " ".join(key_skills)
                    
                    resume_embedding = self.get_embedding(embedding_text)
                    resume["embedding"] = resume_embedding
                
                # Calculate similarity
                similarity = self.calculate_similarity(query_embedding, resume_embedding)
                
                # Add to results
                results.append({
                    "resume_id": resume.get("id"),
                    "name": resume.get("name"),
                    "summary": resume.get("summary"),
                    "key_skills": resume.get("key_skills"),
                    "category": resume.get("category"),
                    "experience_level": resume.get("experience_level"),
                    "total_experience_years": resume.get("total_experience_years"),
                    "similarity_score": similarity
                })
            
            # Sort by similarity score (descending)
            results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            # Return top N results
            return results[:top_n]
        except Exception as e:
            logger.error(f"Error ranking resumes: {str(e)}")
            return []
