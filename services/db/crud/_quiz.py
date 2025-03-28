import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models import QuizResult
from ..connection import get_database_connection

def save_quiz_results(user_id, original_score, enriched_score, detailed_results):
    """Save quiz results to the database"""
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    
    try:
        quiz_result = session.query(QuizResult).filter_by(user_id=user_id).first()
        if quiz_result:
            quiz_result.original_preference = original_score
            quiz_result.enriched_preference = enriched_score
            quiz_result.detailed_results = detailed_results
            quiz_result.updated_at = datetime.datetime.utcnow()
        else:
            quiz_result = QuizResult(
                user_id=user_id,
                original_preference=original_score,
                enriched_preference=enriched_score,
                detailed_results=detailed_results
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
                "detailed_results": quiz_results.detailed_results
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
            "detailed_results": result.detailed_results
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
        quiz_results = session.query(QuizResult).filter_by(user_id=user_id).all()
        return [{
            "original": result.original_preference,
            "enriched": result.enriched_preference,
            "detailed_results": result.detailed_results
        } for result in quiz_results]
    except Exception as e:
        print(f"Error getting quiz results list: {e}")
        return None
    finally:
        session.close()