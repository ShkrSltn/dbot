import datetime
from sqlalchemy.orm import sessionmaker
from ..models import Framework
from ..connection import get_database_connection

def save_framework(name, structure, description=None, is_default=False, created_by=None):
    """Save a framework to the database"""
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    
    try:
        framework = Framework(
            name=name,
            description=description,
            structure=structure,
            is_default=is_default,
            created_by=created_by
        )
        session.add(framework)
        session.commit()
        return framework.id
    except Exception as e:
        session.rollback()
        print(f"Error saving framework: {e}")
        return None
    finally:
        session.close()

def get_framework(framework_id):
    """Get a framework by ID"""
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    
    try:
        framework = session.query(Framework).filter_by(id=framework_id).first()
        if framework:
            return {
                "id": framework.id,
                "name": framework.name,
                "description": framework.description,
                "structure": framework.structure,
                "is_default": framework.is_default,
                "created_by": framework.created_by,
                "created_at": framework.created_at,
                "updated_at": framework.updated_at
            }
        return None
    except Exception as e:
        print(f"Error getting framework: {e}")
        return None
    finally:
        session.close()

def get_all_frameworks():
    """Get all frameworks"""
    db = get_database_connection()
    if not db:
        return []
    
    session = db["Session"]()
    
    try:
        frameworks = session.query(Framework).order_by(Framework.is_default.desc(), Framework.name).all()
        result = []
        for framework in frameworks:
            result.append({
                "id": framework.id,
                "name": framework.name,
                "description": framework.description,
                "structure": framework.structure,
                "is_default": framework.is_default,
                "created_by": framework.created_by,
                "created_at": framework.created_at,
                "updated_at": framework.updated_at
            })
        return result
    except Exception as e:
        print(f"Error getting all frameworks: {e}")
        return []
    finally:
        session.close()

def update_framework(framework_id, name=None, description=None, structure=None):
    """Update a framework"""
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    
    try:
        framework = session.query(Framework).filter_by(id=framework_id).first()
        if not framework:
            return False
        
        if name is not None:
            framework.name = name
        if description is not None:
            framework.description = description
        if structure is not None:
            framework.structure = structure
        
        framework.updated_at = datetime.datetime.utcnow()
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error updating framework: {e}")
        return False
    finally:
        session.close()

def delete_framework(framework_id):
    """Delete a framework"""
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    
    try:
        framework = session.query(Framework).filter_by(id=framework_id).first()
        if not framework:
            return False
        
        # Don't allow deletion of default frameworks
        if framework.is_default:
            return False
        
        session.delete(framework)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error deleting framework: {e}")
        return False
    finally:
        session.close()

def get_framework_by_name(name):
    """Get a framework by name"""
    db = get_database_connection()
    if not db:
        return None
    
    session = db["Session"]()
    
    try:
        framework = session.query(Framework).filter_by(name=name).first()
        if framework:
            return {
                "id": framework.id,
                "name": framework.name,
                "description": framework.description,
                "structure": framework.structure,
                "is_default": framework.is_default,
                "created_by": framework.created_by,
                "created_at": framework.created_at,
                "updated_at": framework.updated_at
            }
        return None
    except Exception as e:
        print(f"Error getting framework by name: {e}")
        return None
    finally:
        session.close() 