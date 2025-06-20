import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..models import Statement
from ..connection import get_database_connection
from services.statement_service import get_category_for_statement

def save_statement(user_id, original_text, enriched_text, metrics):
    """Save a statement to the database"""
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    
    try:
        statement = Statement(
            user_id=user_id,
            original=original_text,
            enriched=enriched_text,
            metrics=metrics
        )
        session.add(statement)
        session.commit()
        return statement.id
    except Exception as e:
        session.rollback()
        print(f"Error saving statement: {e}")
        return None
    finally:
        session.close()

def get_statements(user_id):
    db = get_database_connection()
    if not db:
        return []
    
    session = db["Session"]()
    try:
        statements = session.query(Statement).filter_by(user_id=user_id).all()
        result = []
        for stmt in statements:
            # Get category and subcategory for each statement
            category, subcategory = get_category_for_statement(stmt.original)
            
            result.append({
                "id": stmt.id,
                "original": stmt.original,
                "enriched": stmt.enriched,
                "metrics": stmt.metrics,
                "category": category,
                "subcategory": subcategory,
                "created_at": stmt.created_at
            })
        return result
    except Exception as e:
        print(f"Error getting statements: {e}")
        return []
    finally:
        session.close()

def get_user_statements(user_id):
    """Get all statements for a specific user"""
    db = get_database_connection()
    if not db:
        return []
    
    session = db["Session"]()
    
    try:
        statements = session.query(Statement).filter_by(user_id=user_id).all()
        result = []
        for stmt in statements:
            # Get category and subcategory for each statement
            category, subcategory = get_category_for_statement(stmt.original)
            
            result.append({
                "original": stmt.original,
                "enriched": stmt.enriched,
                "metrics": stmt.metrics,
                "category": category,
                "subcategory": subcategory
            })
        return result
    except Exception as e:
        print(f"Error getting user statements: {e}")
        return []
    finally:
        session.close() 