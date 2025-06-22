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
        # Check if the user exists
        user = session.query(User).filter_by(username=username).first()
        
        if not user:
            # Create new user
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
        # Generate a random password
        random_password = uuid.uuid4().hex
        
        # Create new user
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

def validate_password_strength(password):
    """
    Validate password strength and return feedback
    
    Args:
        password (str): Password to validate
    
    Returns:
        dict: Validation result with strength score and feedback
    """
    if not password:
        return {"valid": False, "score": 0, "feedback": "Password is required"}
    
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 2
    elif len(password) >= 6:
        score += 1
        feedback.append("Consider using at least 8 characters")
    else:
        feedback.append("Password must be at least 6 characters long")
    
    # Character variety checks
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    if has_lower:
        score += 1
    if has_upper:
        score += 1
        if not has_lower:
            feedback.append("Add lowercase letters")
    if has_digit:
        score += 1
    if has_special:
        score += 1
    
    # Provide feedback for missing character types
    if not has_upper and has_lower:
        feedback.append("Add uppercase letters for stronger password")
    if not has_digit:
        feedback.append("Add numbers for stronger password")
    if not has_special:
        feedback.append("Add special characters for stronger password")
    
    # Determine strength level
    if score >= 6:
        strength = "Strong"
    elif score >= 4:
        strength = "Medium"
    elif score >= 2:
        strength = "Weak"
    else:
        strength = "Very Weak"
    
    is_valid = len(password) >= 6  # Minimum requirement
    
    return {
        "valid": is_valid,
        "score": score,
        "strength": strength,
        "feedback": feedback
    }

def register_user(username, password, confirm_password, role="user"):
    """
    Register a new user with username and password validation
    
    Args:
        username (str): Desired username
        password (str): User password
        confirm_password (str): Password confirmation
        role (str): User role (default: "user")
    
    Returns:
        dict: Success status and user data or error message
    """
    # Validate input
    if not username or not password or not confirm_password:
        return {"success": False, "error": "All fields are required"}
    
    if len(username) < 3:
        return {"success": False, "error": "Username must be at least 3 characters long"}
    
    # Use password strength validation
    password_check = validate_password_strength(password)
    if not password_check["valid"]:
        return {"success": False, "error": password_check["feedback"][0] if password_check["feedback"] else "Password is too weak"}
    
    if password != confirm_password:
        return {"success": False, "error": "Passwords do not match"}
    
    # Check for username validity (alphanumeric and underscores only)
    if not username.replace('_', '').isalnum():
        return {"success": False, "error": "Username can only contain letters, numbers, and underscores"}
    
    db = get_database_connection()
    if not db:
        return {"success": False, "error": "Database connection error"}
    
    session = db["Session"]()
    
    try:
        # Check if username already exists
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            return {"success": False, "error": "Username already exists"}
        
        # Create new user
        new_user = User(username=username, role=role)
        new_user.set_password(password)
        
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
        return {"success": False, "error": f"Registration failed: {str(e)}"}
    finally:
        session.close()

def get_user_statistics():
    """
    Get basic statistics about registered users
    
    Returns:
        dict: User statistics including total count, role distribution, recent registrations
    """
    db = get_database_connection()
    if not db:
        return None
        
    session = db["Session"]()
    try:
        # Get total user count
        total_users = session.query(User).count()
        
        # Get role distribution
        admin_count = session.query(User).filter_by(role="admin").count()
        user_count = session.query(User).filter_by(role="user").count()
        
        # Get recent registrations (last 7 days)
        import datetime
        seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
        recent_registrations = session.query(User).filter(User.created_at >= seven_days_ago).count()
        
        return {
            "total_users": total_users,
            "admin_count": admin_count,
            "user_count": user_count,
            "recent_registrations": recent_registrations
        }
    except Exception as e:
        print(f"Error getting user statistics: {e}")
        return None
    finally:
        session.close()

def get_all_users(limit=None):
    """
    Get list of all users (admin function)
    
    Args:
        limit (int, optional): Maximum number of users to return
    
    Returns:
        list: List of user dictionaries
    """
    db = get_database_connection()
    if not db:
        return []
        
    session = db["Session"]()
    try:
        query = session.query(User).order_by(User.created_at.desc())
        
        if limit:
            query = query.limit(limit)
            
        users = query.all()
        
        return [{
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "created_at": user.created_at
        } for user in users]
    except Exception as e:
        print(f"Error getting all users: {e}")
        return []
    finally:
        session.close() 