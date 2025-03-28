from ..connection import get_database_connection
from ..models import ChatMessage

def save_chat_message(user_id, role, content):
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    try:
        message = ChatMessage(
            user_id=user_id,
            role=role,
            content=content
        )
        session.add(message)
        session.commit()
        return True
    except Exception as e:
        print(f"Error saving chat message: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def get_chat_history(user_id):
    db = get_database_connection()
    if not db:
        return []
    
    session = db["Session"]()
    try:
        messages = session.query(ChatMessage).filter_by(user_id=user_id).order_by(ChatMessage.created_at).all()
        history = []
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content
            })
        return history
    except Exception as e:
        print(f"Error getting chat history: {e}")
        return []
    finally:
        session.close() 