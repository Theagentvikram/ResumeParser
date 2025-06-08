import os
import numpy as np
import requests
from typing import List, Dict, Any
import httpx
from sklearn.metrics.pairwise import cosine_similarity

# Get HF API token from environment
HF_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_EMBEDDING_API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/all-MiniLM-L6-v2"

async def get_embedding(text: str) -> List[float]:
    """
    Get embedding vector for a piece of text using Hugging Face API
    
    Args:
        text: The text to embed
        
    Returns:
        List of floats representing the embedding vector
    """
    try:
        if HF_API_KEY:
            # Use the API to get embeddings
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    HF_EMBEDDING_API_URL,
                    headers={"Authorization": f"Bearer {HF_API_KEY}"},
                    json={"inputs": text[:2000]}  # Truncate to avoid token limits
                )
                
                if response.status_code == 200:
                    # API returns a list of embeddings, we just need the first one
                    embedding = response.json()[0]
                    return embedding
                else:
                    print(f"Error from HF API: {response.text}")
                    # Fall back to mock embeddings
                    return generate_mock_embedding()
        else:
            print("WARNING: No HF API key found. Using mock embeddings.")
            return generate_mock_embedding()
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return generate_mock_embedding()

def generate_mock_embedding(dimension: int = 384) -> List[float]:
    """
    Generate a mock embedding for testing when API is not available
    
    Args:
        dimension: Embedding dimension (default 384 for all-MiniLM-L6-v2)
        
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