from ..connection import get_database_connection
from ..models import PromptHistory

def save_prompt_history(user_id, prompt_name, prompt_content, original_statement, 
                       enriched_statement, settings, metrics=None, evaluation_result=None, attempts=1):
    """
    Save a prompt history entry to the database
    
    Args:
        user_id: ID of the user
        prompt_name: Name of the prompt used
        prompt_content: Full prompt template content
        original_statement: Original statement that was tested
        enriched_statement: Result after enrichment
        settings: Settings used (length, profile, evaluation settings, etc.)
        metrics: Quality metrics and scores
        evaluation_result: AI evaluation result if available
        attempts: Number of attempts made
        
    Returns:
        ID of the saved prompt history entry or None if failed
    """
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    try:
        prompt_history = PromptHistory(
            user_id=user_id,
            prompt_name=prompt_name,
            prompt_content=prompt_content,
            original_statement=original_statement,
            enriched_statement=enriched_statement,
            settings=settings,
            metrics=metrics,
            evaluation_result=evaluation_result,
            attempts=attempts
        )
        session.add(prompt_history)
        session.commit()
        return prompt_history.id
    except Exception as e:
        session.rollback()
        print(f"Error saving prompt history: {e}")
        return None
    finally:
        session.close()

def get_user_prompt_history(user_id, limit=None):
    """
    Get prompt history for a specific user
    
    Args:
        user_id: ID of the user
        limit: Maximum number of entries to return (None for all)
        
    Returns:
        List of prompt history entries
    """
    db = get_database_connection()
    if not db:
        return []
    
    session = db["Session"]()
    try:
        query = session.query(PromptHistory).filter_by(user_id=user_id).order_by(PromptHistory.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        history_entries = query.all()
        result = []
        for entry in history_entries:
            result.append({
                "id": entry.id,
                "prompt_name": entry.prompt_name,
                "prompt_content": entry.prompt_content,
                "original_statement": entry.original_statement,
                "enriched_statement": entry.enriched_statement,
                "settings": entry.settings,
                "metrics": entry.metrics,
                "evaluation_result": entry.evaluation_result,
                "attempts": entry.attempts,
                "created_at": entry.created_at
            })
        return result
    except Exception as e:
        print(f"Error getting user prompt history: {e}")
        return []
    finally:
        session.close()

def delete_prompt_history_entry(user_id, entry_id):
    """
    Delete a specific prompt history entry
    
    Args:
        user_id: ID of the user
        entry_id: ID of the entry to delete
        
    Returns:
        Boolean indicating success or failure
    """
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    try:
        entry = session.query(PromptHistory).filter_by(id=entry_id, user_id=user_id).first()
        if entry:
            session.delete(entry)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error deleting prompt history entry: {e}")
        return False
    finally:
        session.close()

def clear_user_prompt_history(user_id):
    """
    Clear all prompt history for a specific user
    
    Args:
        user_id: ID of the user
        
    Returns:
        Number of deleted entries
    """
    db = get_database_connection()
    if not db:
        return 0
    
    session = db["Session"]()
    try:
        entries = session.query(PromptHistory).filter_by(user_id=user_id).all()
        count = len(entries)
        
        for entry in entries:
            session.delete(entry)
        
        session.commit()
        return count
    except Exception as e:
        session.rollback()
        print(f"Error clearing user prompt history: {e}")
        return 0
    finally:
        session.close()

def get_prompt_history_stats(user_id):
    """
    Get statistics about prompt history for a user
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary with statistics
    """
    db = get_database_connection()
    if not db:
        return {}
    
    session = db["Session"]()
    try:
        total_entries = session.query(PromptHistory).filter_by(user_id=user_id).count()
        
        # Get unique prompts used
        unique_prompts = session.query(PromptHistory.prompt_name).filter_by(user_id=user_id).distinct().count()
        
        return {
            "total_entries": total_entries,
            "unique_prompts_tested": unique_prompts
        }
    except Exception as e:
        print(f"Error getting prompt history stats: {e}")
        return {}
    finally:
        session.close()

def get_best_performing_prompts(user_id, metric_key="cosine_embedding", limit=5):
    """
    Get best performing prompts based on a specific metric
    
    Args:
        user_id: ID of the user
        metric_key: Key of the metric to sort by
        limit: Number of top prompts to return
        
    Returns:
        List of best performing prompt history entries
    """
    db = get_database_connection()
    if not db:
        return []
    
    session = db["Session"]()
    try:
        entries = session.query(PromptHistory).filter_by(user_id=user_id).all()
        
        # Filter entries that have the specified metric
        valid_entries = []
        for entry in entries:
            if entry.metrics and metric_key in entry.metrics:
                valid_entries.append({
                    "id": entry.id,
                    "prompt_name": entry.prompt_name,
                    "prompt_content": entry.prompt_content,
                    "original_statement": entry.original_statement,
                    "enriched_statement": entry.enriched_statement,
                    "settings": entry.settings,
                    "metrics": entry.metrics,
                    "evaluation_result": entry.evaluation_result,
                    "attempts": entry.attempts,
                    "created_at": entry.created_at,
                    "metric_value": entry.metrics[metric_key]
                })
        
        # Sort by metric value (descending for most metrics)
        valid_entries.sort(key=lambda x: x["metric_value"], reverse=True)
        
        return valid_entries[:limit]
    except Exception as e:
        print(f"Error getting best performing prompts: {e}")
        return []
    finally:
        session.close() 