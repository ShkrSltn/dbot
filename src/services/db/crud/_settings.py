import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models import GlobalSettings
from ..connection import get_database_connection

def save_user_settings(user_id, settings_data):
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    try:
        # Проверяем, существуют ли настройки
        settings = session.query(GlobalSettings).filter_by(user_id=user_id).first()
        
        if settings:
            # Обновляем существующие настройки
            for key, value in settings_data.items():
                setattr(settings, key, value)
        else:
            # Создаем новые настройки
            settings_data['user_id'] = user_id
            settings = GlobalSettings(**settings_data)
            session.add(settings)
        
        session.commit()
        return True
    except Exception as e:
        print(f"Error saving user settings: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_user_settings(user_id):
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    try:
        settings = session.query(GlobalSettings).filter_by(user_id=user_id).first()
        if settings:
            return {
                "selected_statements": settings.selected_statements,
                "custom_statements": settings.custom_statements
            }
        return None
    except Exception as e:
        print(f"Error getting user settings: {e}")
        return None
    finally:
        session.close()

def get_global_settings(key="user_settings"):
    """Get global settings from database"""
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    
    try:
        settings = session.query(GlobalSettings).filter_by(key=key).first()
        
        if settings:
            return settings.value
        else:
            # Default settings with evaluation settings
            default_settings = {
                "selected_categories": [],
                "custom_statements": [],
                "evaluation_enabled": True,
                "evaluation_max_attempts": 5,
                "selected_prompt_id": 0,
                "competency_questions_enabled": True
            }
            
            # Create settings if they don't exist
            new_settings = GlobalSettings(key=key, value=default_settings)
            session.add(new_settings)
            session.commit()
            
            return default_settings
    except Exception as e:
        print(f"Error getting global settings: {e}")
        return None
    finally:
        session.close()

def save_global_settings(key="user_settings", value=None):
    """Save global settings to database"""
    if value is None:
        return False
        
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    
    try:
        settings = session.query(GlobalSettings).filter_by(key=key).first()
        
        if settings:
            settings.value = value
            settings.updated_at = datetime.datetime.utcnow()
        else:
            settings = GlobalSettings(key=key, value=value)
            session.add(settings)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error saving global settings: {e}")
        return False
    finally:
        session.close() 


def get_competency_questions_enabled():
    """Get competency questions enabled setting from global settings
    
    Returns:
        bool: True if competency questions are enabled, False otherwise
    """
    global_settings = get_global_settings("user_settings")
    if global_settings is None:
        return True  # Default to True if settings not available
    
    return global_settings.get("competency_questions_enabled", True)
