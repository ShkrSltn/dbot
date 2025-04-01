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

# Функция для создания соединения с базой данных
@st.cache_resource
def get_database_engine():
    # Получаем строку подключения из переменных окружения или используем значение по умолчанию
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/digibot")
    
    try:
        # Создаем движок SQLAlchemy
        engine = create_engine(DATABASE_URL)
        
        # Создаем все таблицы, если они не существуют
        Base.metadata.create_all(engine)
        
        return engine
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_database_connection():
    engine = get_database_engine()
    if not engine:
        return None
    
    # Создаем новую сессию для каждого запроса
    Session = sessionmaker(bind=engine)
    
    return {"engine": engine, "Session": Session}

def check_db_connection():
    """Check if database connection is working"""
    try:
        engine = create_engine(os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/digibot'))
        with engine.connect() as connection:
            # Execute a SELECT query using text()
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Database connection error: {str(e)}")
        return False 

def generate_session_token(user_id):
    """Generate a unique session token for a user and store it in the database"""
    token = str(uuid.uuid4())
    
    db = get_database_connection()
    if not db:
        return token
    
    session = db["Session"]()
    try:
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
        session.commit()
        
        return token
    except Exception as e:
        print(f"Error generating session token: {e}")
        session.rollback()
        return token
    finally:
        session.close()

def verify_session_token(user_id, token):
    """Verify that the session token is valid for the given user_id"""
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    try:
        # Проверяем токен в базе данных
        session_record = session.query(UserSession).filter_by(
            user_id=user_id, 
            token=token,
            expired=False
        ).first()
        
        if session_record:
            # Проверяем, не истек ли срок действия токена
            if session_record.expires_at > datetime.datetime.utcnow():
                return True
            else:
                # Помечаем токен как истекший
                session_record.expired = True
                session.commit()
        return False
    except Exception as e:
        print(f"Error verifying session token: {e}")
        return False
    finally:
        session.close() 