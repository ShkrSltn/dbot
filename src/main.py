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
            initial_sidebar_state="expanded"
        )
        
        # Hide default sidebar navigation and customize sidebar behavior
        st.markdown("""
            <style>
            /* Hide default Streamlit navigation */
            [data-testid="stSidebarNav"] {
                display: none !important;
            }
            
            /* Desktop: Sidebar expanded by default */
            @media (min-width: 769px) {
                [data-testid="stSidebar"] {
                    transform: translateX(0) !important;
                    visibility: visible !important;
                }
                [data-testid="stSidebar"] > div:first-child {
                    transform: translateX(0) !important;
                    visibility: visible !important;
                }
                /* Hide collapse button on desktop */
                [data-testid="collapsedControl"] {
                    display: none !important;
                }
            }
            
            /* Mobile: Sidebar collapsed by default */
            @media (max-width: 768px) {
                [data-testid="stSidebar"] {
                    width: 0 !important;
                    transform: translateX(-100%) !important;
                }
                [data-testid="stSidebar"] > div:first-child {
                    transform: translateX(-100%) !important;
                    visibility: hidden !important;
                }
                /* Show collapse control (hamburger menu) on mobile */
                [data-testid="collapsedControl"] {
                    display: block !important;
                    visibility: visible !important;
                    position: fixed !important;
                    top: 0.5rem !important;
                    left: 0.5rem !important;
                    z-index: 999999 !important;
                    background: white !important;
                    border-radius: 4px !important;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
                }
                /* Ensure main content uses full width on mobile */
                .main .block-container {
                    padding-left: 1rem !important;
                    padding-right: 1rem !important;
                    max-width: none !important;
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
            from services.cookie_utils import get_session_cookie, clear_session_cookie
            print("DEBUG: Cookie utilities imported successfully")
        except ImportError as e:
            print(f"DEBUG: Error importing cookie utilities: {e}")
            st.error(f"Error importing cookie utilities: {e}")
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