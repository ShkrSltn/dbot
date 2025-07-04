import pandas as pd
from ..connection import get_database_connection

def get_analytics_data(user_id=None):
    db = get_database_connection()
    if not db:
        return None
    
    engine = db["engine"]
    
    try:
        # If user_id is specified, get data only for this user
        user_filter = f"WHERE user_id = {user_id}" if user_id else ""
        
        # Get statistics for enriched statements
        statements_df = pd.read_sql(
            f"SELECT * FROM statements {user_filter}",
            engine
        )
        
        # Get statistics for quiz results
        quiz_results_df = pd.read_sql(
            f"SELECT * FROM quiz_results {user_filter}",
            engine
        )
        
        # Get statistics for chat messages
        chat_messages_df = pd.read_sql(
            f"SELECT * FROM chat_messages {user_filter}",
            engine
        )
        
        return {
            "statements": statements_df,
            "quiz_results": quiz_results_df,
            "chat_messages": chat_messages_df
        }
    except Exception as e:
        print(f"Error getting analytics data: {e}")
        return None 