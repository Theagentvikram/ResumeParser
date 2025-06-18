import os
import numpy as np
import requests
from typing import List, Dict, Any
import httpx
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get OpenRouter API token from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_EMBEDDING_API_URL = "https://openrouter.ai/api/v1/embeddings"

async def get_embedding(text: str) -> List[float]:
    """
    Get embedding vector for a piece of text using OpenRouter API with Mistral Instruct model
    
    Args:
        text: The text to embed
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        if OPENROUTER_API_KEY:
            # Use the API to get embeddings
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    OPENROUTER_EMBEDDING_API_URL,
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "HTTP-Referer": "https://github.com/theagentvikram/ResuMatch",  # Required by OpenRouter
                        "X-Title": "ResuMatch"  # Optional but helpful for OpenRouter
                    },
                    json={
                        "model": "mistralai/mistral-7b-instruct:free",  # Using free version of Mistral Instruct
                        "input": text[:2000]  # Truncate to avoid token limits
                    }
                )
                
                if response.status_code == 200:
                    # API returns a list of embeddings, we just need the first one
                    embedding = response.json()["data"][0]["embedding"]
                    return embedding
                else:
                    print(f"Error from OpenRouter API: {response.text}")
                    # Fall back to mock embeddings
                    return generate_mock_embedding()
        else:
            print("WARNING: No OpenRouter API key found. Using mock embeddings.")
            return generate_mock_embedding()
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return generate_mock_embedding()

def generate_mock_embedding(dimension: int = 4096) -> List[float]:
    """
    Generate a mock embedding for testing when API is not available
    
    Args:
        dimension: Embedding dimension (default 4096 for Mistral)
        
    Returns:
        Mock embedding vector of specified dimension
    """
    # Generate random vector and normalize it
    vector = np.random.normal(0, 1, dimension)
    normalized = vector / np.linalg.norm(vector)
    return normalized.tolist()

def calculate_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
        
    Returns:
        Cosine similarity score (float between -1 and 1)
    """
    # Convert to numpy arrays and reshape for cosine_similarity
    v1 = np.array(embedding1).reshape(1, -1)
    v2 = np.array(embedding2).reshape(1, -1)
    
    # Calculate cosine similarity
    similarity = cosine_similarity(v1, v2)[0][0]
    return float(similarity)

async def rank_documents_by_query(
    query_embedding: List[float],
    documents: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Rank documents by similarity to query
    
    Args:
        query_embedding: Embedding of the search query
        documents: List of documents with 'embedding' field
        
    Returns:
        List of documents sorted by similarity to query
    """
    # Calculate similarity for each document
    for doc in documents:
        doc['similarity'] = calculate_similarity(query_embedding, doc['embedding'])
    
    # Sort by similarity (highest first)
    sorted_docs = sorted(documents, key=lambda x: x['similarity'], reverse=True)
    return sorted_docs 