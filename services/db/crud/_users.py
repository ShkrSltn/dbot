import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models import User
from ..connection import get_database_connection

def save_user(username, role="user"):
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    try:
        # Проверяем, существует ли пользователь
        user = session.query(User).filter_by(username=username).first()
        
        if not user:
            # Создаем нового пользователя
            user = User(username=username, role=role)
            session.add(user)
            session.commit()
        
        return user.id
    except Exception as e:
        print(f"Error saving user: {e}")
        session.rollback()
        return None
    finally:
        session.close()

def get_user(user_id):
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            return {"id": user.id, "username": user.username, "role": user.role}
        return None
    except Exception as e:
        print(f"Error getting user: {e}")
        return None
    finally:
        session.close()

def authenticate_user(username, password):
    db = get_database_connection()
    if not db:
        return {"success": False, "error": "Database connection error"}
    
    session = db["Session"]()
    
    try:
        user = session.query(User).filter_by(username=username).first()
        if user and user.check_password(password):
            return {"success": True, "user": {"id": user.id, "username": user.username, "role": user.role}}
        return {"success": False, "error": "Invalid credentials"}
    finally:
        session.close()

def create_anonymous_user(username):
    """Creates an anonymous user with a random password"""
    db = get_database_connection()
    if not db:
        return {"success": False, "error": "Database connection error"}
    
    session = db["Session"]()
    
    try:
        # Генерируем случайный пароль
        random_password = uuid.uuid4().hex
        
        # Создаем нового пользователя
        new_user = User(username=username, role="user")
        new_user.set_password(random_password)
        
        session.add(new_user)
        session.commit()
        
        return {
            "success": True,
            "user": {
                "id": new_user.id,
                "username": new_user.username,
                "role": new_user.role
            }
        }
    except Exception as e:
        session.rollback()
        return {"success": False, "error": str(e)}
    finally:
        session.close()

def get_user_by_id(user_id):
    """Get user by ID from database"""
    db = get_database_connection()
    if not db:
        return None
        
    session = db["Session"]()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if user:
            return {
                "id": user.id,
                "username": user.username,
                "role": user.role
            }
        return None
    except Exception as e:
        print(f"Error getting user by ID: {e}")
        return None
    finally:
        session.close() 