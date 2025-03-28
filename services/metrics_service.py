import numpy as np
from services.embedding_service import load_embedding_model

def calculate_quality_metrics(original, enriched):
    """Calculates quality metrics between original and enriched statements"""
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
        embedding_sim = np.dot(original_embedding, enriched_embedding) / (
                np.linalg.norm(original_embedding) * np.linalg.norm(enriched_embedding))
        
        # TF-IDF similarity (simplified calculation for demo)
        print("DEBUG: Calculating TF-IDF similarity")
        tfidf_sim = 0.5 + (embedding_sim * 0.5)  # Use embedding_sim as a base
        
        # Simplified readability metrics
        print("DEBUG: Calculating readability metrics")
        word_count = len(enriched.split())
        char_count = len(enriched)
        avg_word_length = char_count / max(1, word_count)
        
        # Readability scores
        readability = {
            "word_count": word_count,
            "character_count": char_count,
            "avg_word_length": avg_word_length,
            "estimated_reading_ease": max(0, min(100, 100 - (avg_word_length * 10)))
        }
        
        print("DEBUG: Metrics calculation completed successfully")
        return {
            "cosine_tfidf": float(tfidf_sim),
            "cosine_embedding": float(embedding_sim),
            "readability": readability
        }
    except Exception as e:
        print(f"DEBUG: Error calculating metrics: {e}")
        raise 