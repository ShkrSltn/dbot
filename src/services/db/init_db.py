import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, User, GlobalSettings
import datetime
from .connection import get_database_connection

def init_db():
    """Initialize database tables and default data"""
    db = get_database_connection()
    if not db:
        return False
    
    engine = db["engine"]
    
    try:
        # Create all tables
        Base.metadata.create_all(engine)
        
        # Create session
        Session = db["Session"]
        session = Session()
        
        # Check if admin users exist
        admin_count = session.query(User).filter_by(role="admin").count()
        
        if admin_count == 0:
            # Create default admin users
            admin1 = User(username="admin1", role="admin")
            admin1.set_password("admin1pass")
            
            admin2 = User(username="admin2", role="admin")
            admin2.set_password("admin2pass")
            
            # Create default regular users
            user1 = User(username="user1", role="user")
            user1.set_password("user1pass")
            
            user2 = User(username="user2", role="user")
            user2.set_password("user2pass")
            
            # Add all users
            session.add_all([admin1, admin2, user1, user2])
            
            # Create default global settings
            default_settings = GlobalSettings(
                key="user_settings",
                value={
                                    "selected_categories": [],
                "custom_statements": []
                }
            )
            session.add(default_settings)
            
            # Commit changes
            session.commit()
            print("DEBUG: Created default users and settings")
            
        session.close()
        return True
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False 