import streamlit as st
import sys
import traceback
import os
from dotenv import load_dotenv
from services.db.connection import check_db_connection
from services.db.init_db import init_db

# Load environment variables
load_dotenv()

# Add debug information
print("DEBUG: Starting main.py execution")
print(f"DEBUG: Python version: {sys.version}")
print(f"DEBUG: Streamlit version: {st.__version__}")
print(f"DEBUG: Database URL: {os.getenv('DATABASE_URL', 'Not set - using default')}")

def initialize_app():
    """Initialize application and data base"""
    try:
        # Configure page settings
        print("DEBUG: About to call set_page_config")
        st.set_page_config(
            page_title="DigiBot",
            page_icon=":robot:",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        # Hide default sidebar navigation and customize sidebar behavior on mobile
        st.markdown("""
            <style>
            [data-testid="stSidebarNav"] {
                display: none;
            }
            /* Disable automatic sidebar expansion on mobile */
            @media (max-width: 640px) {
                .st-emotion-cache-1cypcdb .st-emotion-cache-1egp7fm {
                    margin-top: 0;
                }
                /* Force sidebar to stay collapsed on mobile */
                [data-testid="collapsedControl"] {
                    display: block;
                }
                /* Remove sidebar auto-expansion */
                .st-emotion-cache-uf99v8 {
                    display: none;
                }
            }
            </style>
        """, unsafe_allow_html=True)
        
        print("DEBUG: set_page_config called successfully")
        
        # Check database connection
        if not check_db_connection():
            st.error("Failed to connect to database. Please check your database configuration.")
            return False
            
        # Initialize database
        print("DEBUG: Initializing database")
        init_db()
        print("DEBUG: Database initialized")
        
        # Make sure all required page modules are available
        try:
            from pages.profile_builder import display_profile_builder
            from pages.enrichment_demo import display_enrichment_demo
            from pages.batch_enrichment import display_batch_enrichment
            from pages.quiz import display_quiz
            print("DEBUG: All legacy page modules imported successfully")
        except ImportError as e:
            print(f"DEBUG: Error importing page modules: {e}")
            st.error(f"Error importing page modules: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"DEBUG: Error in initialization: {str(e)}")
        print(traceback.format_exc())
        st.error(f"Error in initialization: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        # Initialize application
        if not initialize_app():
            st.stop()
            
        # Import run_app only after successful initialization
        print("DEBUG: About to import run_app from app")
        from app import run_app
        print("DEBUG: run_app imported successfully")
        
        # Run the application
        print("DEBUG: About to call run_app()")
        run_app()
        print("DEBUG: run_app() completed")
        
    except Exception as e:
        print(f"DEBUG: Error in application: {str(e)}")
        print(traceback.format_exc())
        st.error(f"Error in application: {str(e)}")