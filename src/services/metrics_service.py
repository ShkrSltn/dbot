import numpy as np
from services.embedding_service import load_embedding_model
from typing import Dict, Any, Optional
import re
from collections import Counter

def calculate_quality_metrics(original: str, enriched: str) -> Dict[str, Any]:
    """
    Calculates quality metrics between original and enriched statements.
    
    Args:
        original: The original text content
        enriched: The enriched/enhanced text content
        
    Returns:
        Dictionary containing similarity and readability metrics
        
    Raises:
        ValueError: If empty strings are provided
    """
    try:
        print("DEBUG: Starting calculate_quality_metrics")
        # Check for empty strings
        if not original or not enriched:
            raise ValueError("Empty string provided for metrics calculation")

        # Embedding similarity using OpenAI embeddings
        print("DEBUG: Loading embedding model")
        embedding_model = load_embedding_model()
        
        # Get embeddings
        print("DEBUG: Getting embeddings for original text")
        original_embedding = embedding_model.embed_query(original)
        print("DEBUG: Getting embeddings for enriched text")
        enriched_embedding = embedding_model.embed_query(enriched)
        
        # Calculate cosine similarity
        print("DEBUG: Calculating cosine similarity")
        embedding_sim = calculate_cosine_similarity(original_embedding, enriched_embedding)
        
        # TF-IDF similarity (improved calculation)
        print("DEBUG: Calculating TF-IDF similarity")
        tfidf_sim = calculate_tfidf_similarity(original, enriched)
        
        # Enhanced readability metrics
        print("DEBUG: Calculating readability metrics")
        readability = calculate_readability_metrics(enriched)
        
        print("DEBUG: Metrics calculation completed successfully")
        return {
            "cosine_tfidf": float(tfidf_sim),
            "cosine_embedding": float(embedding_sim),
            "readability": readability
        }
    except Exception as e:
        print(f"DEBUG: Error calculating metrics: {e}")
        raise 

def calculate_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

def calculate_tfidf_similarity(text1: str, text2: str) -> float:
    """Calculate a more accurate TF-IDF based similarity."""
    # Tokenize texts
    tokens1 = re.findall(r'\b\w+\b', text1.lower())
    tokens2 = re.findall(r'\b\w+\b', text2.lower())
    
    # Calculate term frequencies
    tf1 = Counter(tokens1)
    tf2 = Counter(tokens2)
    
    # Get all unique terms
    all_terms = set(tokens1) | set(tokens2)
    
    # Calculate dot product and magnitudes
    dot_product = sum(tf1.get(term, 0) * tf2.get(term, 0) for term in all_terms)
    magnitude1 = np.sqrt(sum(tf1.get(term, 0) ** 2 for term in all_terms))
    magnitude2 = np.sqrt(sum(tf2.get(term, 0) ** 2 for term in all_terms))
    
    # Calculate cosine similarity
    if magnitude1 * magnitude2 == 0:
        return 0.0
    
    return dot_product / (magnitude1 * magnitude2)

def calculate_readability_metrics(text: str) -> Dict[str, Any]:
    """Calculate comprehensive readability metrics."""
    # Basic counts
    word_count = len(re.findall(r'\b\w+\b', text))
    char_count = len(text)
    sentence_count = max(1, len(re.split(r'[.!?]+', text)) - 1)
    
    # Average calculations
    avg_word_length = char_count / max(1, word_count)
    avg_sentence_length = word_count / max(1, sentence_count)
    
    # Flesch Reading Ease score (simplified)
    reading_ease = 206.835 - (1.015 * avg_sentence_length) - (84.6 * (char_count / max(1, word_count) / 5))
    reading_ease = max(0, min(100, reading_ease))
    
    return {
        "word_count": word_count,
        "character_count": char_count,
        "avg_word_length": avg_word_length,
        "avg_sentence_length": avg_sentence_length,
        "estimated_reading_ease": float(reading_ease)
    } 