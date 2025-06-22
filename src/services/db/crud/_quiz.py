import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models import QuizResult
from ..connection import get_database_connection
from services.db.crud._settings import get_competency_questions_enabled

def save_quiz_results(user_id, original_score, enriched_score, neither_score, detailed_results, competency_results=None, is_final=False):
    """
    Save quiz results to the database
    
    Parameters:
    - user_id: ID of the user
    - original_score: Score for original statements
    - enriched_score: Score for enriched statements
    - neither_score: Score for "neither" preference
    - detailed_results: Detailed breakdown of results
    - competency_results: Results of competency assessment
    - is_final: Flag indicating if this is the final submission for this quiz attempt
    
    Returns:
    - True if successful, False otherwise
    """
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    
    try:
        # Check if we have an in-progress quiz for this user
        # We'll use the created_at timestamp to identify quiz attempts
        # If the most recent quiz is from the last hour and is_final is False,
        # we'll update it instead of creating a new one
        
        if not is_final:
            # For intermediate saves, just return success without creating a record
            # This prevents creating multiple records during a single quiz attempt
            return True
        
        # Get current datetime for both created_at and updated_at
        current_datetime = datetime.datetime.utcnow()
        
        # Проверка, включены ли вопросы компетенций
        competency_enabled = get_competency_questions_enabled()
        
        # Если компетенции отключены, используем пустой список
        if not competency_enabled:
            competency_results = []
        
        # For final submission, create a new record with proper competency_results handling
        quiz_result = QuizResult(
            user_id=user_id,
            original_preference=original_score,
            enriched_preference=enriched_score,
            neither_preference=neither_score,
            detailed_results=detailed_results,
            competency_results=competency_results or [],  # Убедимся, что competency_results - это список, даже если None
            created_at=current_datetime,
            updated_at=current_datetime
        )
        session.add(quiz_result)
        
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error saving quiz results: {e}")
        return False
    finally:
        session.close()

def get_quiz_results(user_id):
    """Get quiz results for a specific user"""
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    
    try:
        quiz_results = session.query(QuizResult).filter_by(user_id=user_id).first()
        if quiz_results:
            return {
                "original": quiz_results.original_preference,
                "enriched": quiz_results.enriched_preference,
                "neither": quiz_results.neither_preference,
                "detailed_results": quiz_results.detailed_results,
                "created_at": quiz_results.created_at,
                "updated_at": quiz_results.updated_at
            }
        return None
    except Exception as e:
        print(f"Error getting quiz results: {e}")
        return None
    finally:
        session.close()

def get_quiz_results_all_users():
    """Get quiz results for all users"""
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    
    try:
        quiz_results = session.query(QuizResult).all()
        return [{
            "original": result.original_preference,
            "enriched": result.enriched_preference,
            "neither": result.neither_preference,
            "detailed_results": result.detailed_results,
            "competency_results": result.competency_results,
            "created_at": result.created_at,
            "updated_at": result.updated_at
        } for result in quiz_results]
    except Exception as e:
        print(f"Error getting all quiz results: {e}")
        return None
    finally:
        session.close()

def get_quiz_results_list(user_id):
    """Get quiz results for a specific user"""
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    
    try:
        quiz_results = session.query(QuizResult).filter_by(user_id=user_id).order_by(QuizResult.created_at.desc()).all()
        return [{
            "original": result.original_preference,
            "enriched": result.enriched_preference,
            "neither": result.neither_preference,
            "detailed_results": result.detailed_results,
            "competency_results": result.competency_results,
            "created_at": result.created_at,
            "updated_at": result.updated_at
        } for result in quiz_results]
    except Exception as e:
        print(f"Error getting quiz results list: {e}")
        return None
    finally:
        session.close()

def get_available_quiz_dates():
    """Get all available dates from quiz results for date filtering"""
    db = get_database_connection()
    if not db:
        return []
    
    session = db["Session"]()
    
    try:
        # Get distinct dates from quiz results
        dates_query = session.query(QuizResult.created_at).distinct().all()
        dates = []
        for date_tuple in dates_query:
            if date_tuple[0]:  # Check if created_at is not None
                # Convert datetime to date for filtering
                date_only = date_tuple[0].date()
                if date_only not in dates:
                    dates.append(date_only)
        
        # Sort dates in descending order (newest first)
        dates.sort(reverse=True)
        return dates
    except Exception as e:
        print(f"Error getting available quiz dates: {e}")
        return []
    finally:
        session.close()

def get_quiz_results_by_date_range(start_date=None, end_date=None):
    """Get quiz results filtered by date range"""
    db = get_database_connection()
    if not db:
        return []
    
    session = db["Session"]()
    
    try:
        query = session.query(QuizResult)
        
        # Apply date filters if provided
        if start_date:
            # Convert date to datetime for comparison (start of day)
            start_datetime = datetime.datetime.combine(start_date, datetime.time.min)
            query = query.filter(QuizResult.created_at >= start_datetime)
        
        if end_date:
            # Convert date to datetime for comparison (end of day)
            end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
            query = query.filter(QuizResult.created_at <= end_datetime)
        
        quiz_results = query.all()
        
        return [{
            "original": result.original_preference,
            "enriched": result.enriched_preference,
            "neither": result.neither_preference,
            "detailed_results": result.detailed_results,
            "competency_results": result.competency_results,
            "created_at": result.created_at,
            "updated_at": result.updated_at
        } for result in quiz_results]
    except Exception as e:
        print(f"Error getting quiz results by date range: {e}")
        return []
    finally:
        session.close()