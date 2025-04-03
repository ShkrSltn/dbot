from ..connection import get_database_connection
from ..models import Prompt

def save_prompt(user_id, name, content):
    """
    Save a prompt to the database
    
    Args:
        user_id: ID of the user
        name: Name of the prompt
        content: Content of the prompt
        
    Returns:
        ID of the saved prompt or None if failed
    """
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    try:
        # Check if prompt with this name already exists for this user
        existing_prompt = session.query(Prompt).filter_by(user_id=user_id, name=name).first()
        
        if existing_prompt:
            # Update existing prompt
            existing_prompt.content = content
            session.commit()
            return existing_prompt.id
        else:
            # Create new prompt
            prompt = Prompt(
                user_id=user_id,
                name=name,
                content=content
            )
            session.add(prompt)
            session.commit()
            return prompt.id
    except Exception as e:
        session.rollback()
        print(f"Error saving prompt: {e}")
        return None
    finally:
        session.close()

def get_user_prompts(user_id):
    """
    Get all prompts for a specific user
    
    Args:
        user_id: ID of the user
        
    Returns:
        Dictionary of prompt names and contents
    """
    db = get_database_connection()
    if not db:
        return {}
    
    session = db["Session"]()
    try:
        prompts = session.query(Prompt).filter_by(user_id=user_id).all()
        result = {}
        for prompt in prompts:
            result[prompt.name] = prompt.content
        return result
    except Exception as e:
        print(f"Error getting user prompts: {e}")
        return {}
    finally:
        session.close()

def delete_prompt(user_id, name):
    """
    Delete a prompt
    
    Args:
        user_id: ID of the user
        name: Name of the prompt to delete
        
    Returns:
        Boolean indicating success or failure
    """
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    try:
        prompt = session.query(Prompt).filter_by(user_id=user_id, name=name).first()
        if prompt:
            session.delete(prompt)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error deleting prompt: {e}")
        return False
    finally:
        session.close()

def get_all_prompts():
    """
    Get all prompts from the database
    
    Returns:
        List of dictionaries with prompt information
    """
    db = get_database_connection()
    if not db:
        return []
    
    session = db["Session"]()
    try:
        prompts = session.query(Prompt).all()
        result = []
        for prompt in prompts:
            result.append({
                "id": prompt.id,
                "user_id": prompt.user_id,
                "name": prompt.name,
                "content": prompt.content,
                "created_at": prompt.created_at
            })
        return result
    except Exception as e:
        print(f"Error getting all prompts: {e}")
        return []
    finally:
        session.close()