import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import streamlit as st
from dotenv import load_dotenv
from .models import Base, UserSession
import datetime
import uuid

# Load environment variables
load_dotenv()

# Function to create a database connection optimized for Cloud Run
def get_database_engine():
    """Create database engine optimized for Cloud Run with no connection pooling"""
    # Get the database connection string from environment variables or use the default value
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/digibot")
    
    try:
        # Create the SQLAlchemy engine with Cloud Run optimized settings
        # No connection pooling - create and close connections per request
        engine = create_engine(
            DATABASE_URL,
            # Cloud Run optimization: no connection pooling
            poolclass=None,                 # Disable connection pooling completely
            connect_args={
                "connect_timeout": 10,      # Quick connection timeout
                "application_name": "digibot_streamlit"
            }
        )
        
        # Create all tables if they don't exist (only once)
        Base.metadata.create_all(engine)
        
        return engine
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_database_connection():
    """Get a fresh database connection for each request (Cloud Run optimized)"""
    engine = get_database_engine()
    if not engine:
        return None
    
    # Create a new session for each request with auto-close behavior
    Session = sessionmaker(
        bind=engine,
        autoflush=False,        # Don't auto-flush to avoid unexpected commits
        autocommit=False        # Explicit transaction control
    )
    
    return {"engine": engine, "Session": Session}

def get_db_session():
    """Context manager for database sessions - automatically closes connections"""
    from contextlib import contextmanager
    
    @contextmanager
    def session_scope():
        """Provide a transactional scope around a series of operations."""
        db = get_database_connection()
        if not db:
            yield None
            return
            
        session = db["Session"]()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Database session error: {e}")
            raise
        finally:
            session.close()
            # Dispose engine to free all connections
            db["engine"].dispose()
    
    return session_scope()

def check_db_connection():
    """Check if database connection is working (Cloud Run optimized)"""
    try:
        # Use the same optimized settings as main engine
        DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/digibot')
        engine = create_engine(
            DATABASE_URL,
            poolclass=None,  # No connection pooling
            connect_args={"connect_timeout": 10}
        )
        
        with engine.connect() as connection:
            # Execute a SELECT query using text()
            connection.execute(text("SELECT 1"))
        
        # Explicitly dispose engine to free resources
        engine.dispose()
        return True
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return False 

def generate_session_token(user_id):
    """Generate a unique session token for a user and store it in the database"""
    token = str(uuid.uuid4())
    
    try:
        with get_db_session() as session:
            if session is None:
                return token
            
            # Create expiration time (24 hours from now)
            expires_at = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            
            # Create new session record
            user_session = UserSession(
                user_id=user_id,
                token=token,
                expires_at=expires_at,
                expired=False
            )
            
            session.add(user_session)
            # Commit is handled by context manager
            
        return token
    except Exception as e:
        print(f"Error generating session token: {e}")
        return token

def verify_session_token(user_id, token):
    """Verify that the session token is valid for the given user_id"""
    try:
        with get_db_session() as session:
            if session is None:
                return False
            
            # Check the token in the database
            session_record = session.query(UserSession).filter_by(
                user_id=user_id, 
                token=token,
                expired=False
            ).first()
            
            if session_record:
                # Check if the token has expired
                if session_record.expires_at > datetime.datetime.utcnow():
                    return True
                else:
                    # Mark the token as expired
                    session_record.expired = True
                    # Commit is handled by context manager
            return False
    except Exception as e:
        print(f"Error verifying session token: {e}")
        return False

# Example usage for other parts of the application:
# 
# Instead of:
# db = get_database_connection()
# session = db["Session"]()
# try:
#     # your database operations
#     session.commit()
# except:
#     session.rollback()
# finally:
#     session.close()
#
# Use this Cloud Run optimized approach:
# with get_db_session() as session:
#     if session:
#         # your database operations
#         # commit/rollback handled automatically 