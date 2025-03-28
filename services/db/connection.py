import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import streamlit as st
from dotenv import load_dotenv
from .models import Base

# Load environment variables
load_dotenv()

# Функция для создания соединения с базой данных
@st.cache_resource
def get_database_connection():
    # Получаем строку подключения из переменных окружения или используем значение по умолчанию
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/digibot")
    
    try:
        # Создаем движок SQLAlchemy
        engine = create_engine(DATABASE_URL)
        
        # Создаем все таблицы, если они не существуют
        Base.metadata.create_all(engine)
        
        # Создаем фабрику сессий
        Session = sessionmaker(bind=engine) 
        
        return {"engine": engine, "Session": Session}
    except Exception as e:
        print(f"Error connecting to database: {e}")
        # В случае ошибки возвращаем None
        return None

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