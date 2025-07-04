import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import datetime

# Import service functions
from services.service import (
    load_llm, 
    load_embedding_model, 
    enrich_statement_with_llm,
    calculate_quality_metrics,
    get_sample_statements,
    get_statements_from_settings,
    get_all_statements,
    generate_chat_response,
    save_chat_message,
    get_chat_history,
    save_statement,
    save_quiz_results,
    get_quiz_results,
    save_profile,
    get_profile,
    get_global_settings,
    save_global_settings,
    get_user_by_id,
    verify_session_token
)

# Import cookie utilities with enhanced functions
from services.cookie_utils import (
    get_session_data, 
    clear_session_data, 
    get_session_from_state, 
    clear_session_from_state,
    set_current_page,
    get_current_page,
    ensure_session_persistence,
    restore_session_on_startup,
    # Legacy aliases for compatibility
    get_session_cookie, 
    clear_session_cookie,
    set_current_page_cookie,
    get_current_page_cookie
)

# Import page display functions
from pages.home import display_home_page
from pages.analytics import display_analytics
from pages.user_page.user_flow import display_user_flow
from pages.user_settings import display_user_settings
from pages.prompt_engineer import display_prompt_engineer
from pages.user_management import display_user_management

# Import database connection and models
from services.db.connection import get_database_connection
from services.db.models import UserSession

# Import new service
from services.profile_evaluation_service import evaluate_profile_with_ai

def verify_session_token(user_id, token):
    """Verify that the session token is valid for the given user_id"""
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    try:
        # Check token in the database
        session_record = session.query(UserSession).filter_by(
            user_id=user_id, 
            token=token,
            expired=False
        ).first()
        
        if session_record:
            # Check if the token has expired
            if session_record.expires_at > datetime.datetime.utcnow():
                return True
            else:
                # Mark the token as expired
                session_record.expired = True
                session.commit()
        return False
    except Exception as e:
        print(f"Error verifying session token: {e}")
        return False
    finally:
        session.close()

def run_app():
    print(f"DEBUG: run_app() started")
    
    # Hide default sidebar navigation and customize responsive behavior
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
        
        /* User logout button styling for better mobile UX */
        
        /* Enhanced footer logout button appearance */
        [data-testid="column"] .stButton button {
            font-size: 1rem !important;
            padding: 0.5rem 1.5rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Get sample statements before page routing
    sample_statements = get_sample_statements()

    # Initialize session state for authentication if not exists
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.current_role = None
        st.session_state.user = None

    # Enhanced session restoration on startup
    if not st.session_state.authenticated:
        print("DEBUG: Attempting to restore session on startup...")
        
        # Try the enhanced restoration function
        restored_session = restore_session_on_startup()
        
        if restored_session and 'user_id' in restored_session and 'session_token' in restored_session:
            user_id = restored_session['user_id']
            session_token = restored_session['session_token']
            
            print(f"DEBUG: Found session data for user {user_id}")
            
            # Verify session token is valid for this user
            if verify_session_token(int(user_id), session_token):
                print(f"DEBUG: Session token verified for user {user_id}")
                
                # Try to get user from database
                user = get_user_by_id(int(user_id))
                if user:
                    print(f"DEBUG: User found in database: {user['username']}")
                    st.session_state.authenticated = True
                    st.session_state.user = user
                    st.session_state.current_role = user["role"]
                    
                    # Ensure persistence for future reloads
                    ensure_session_persistence()
                    
                    print(f"DEBUG: Authentication restored successfully for {user['username']}")
                else:
                    print("DEBUG: User not found in database")
                    clear_session_data()
                    clear_session_from_state()
            else:
                print("DEBUG: Session token verification failed")
                # Clear invalid session data
                clear_session_data()
                clear_session_from_state()
        else:
            print("DEBUG: No valid session data found")

    # Check authentication
    if not st.session_state.authenticated:
        from pages.auth import display_auth
        display_auth()
        return

    # Initialize user data if not exists
    if 'user' not in st.session_state:
        st.session_state.user = {
            "id": 1,
            "username": "demo_user",
            "role": st.session_state.current_role
        }

    # Load user profile from database
    if 'profile' not in st.session_state:
        user_profile = get_profile(st.session_state.user["id"])
        if user_profile:
            st.session_state.profile = user_profile
        else:
            st.session_state.profile = {
                "job_role": "",
                "job_domain": "",
                "years_experience": 0,
                "digital_proficiency": "Intermediate",
                "primary_tasks": ""
            }

    # Load user statements from database
    if 'enriched_statements' not in st.session_state:
        # Always start with empty statements - let the system generate fresh ones based on settings
        # This prevents showing old/accumulated statements and ensures consistency with current settings
        st.session_state.enriched_statements = []
        
    # Load quiz results from database
    if 'quiz_results' not in st.session_state:
        user_quiz_results = get_quiz_results(st.session_state.user["id"])
        if user_quiz_results:
            st.session_state.quiz_results = {
                "original": user_quiz_results["original"],
                "enriched": user_quiz_results["enriched"]
            }
            st.session_state.detailed_quiz_results = user_quiz_results["detailed_results"]
            
            # Set quiz_completed flag based on whether there are any results
            total_responses = user_quiz_results["original"] + user_quiz_results["enriched"]
            st.session_state.quiz_completed = total_responses > 0
        else:
            st.session_state.quiz_results = {"original": 0, "enriched": 0}
            st.session_state.detailed_quiz_results = {
                "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
            }
            st.session_state.quiz_completed = False

    # Initialize chat history if not exists
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Load global user settings
    if 'user_settings' not in st.session_state:
        global_settings = get_global_settings("user_settings")
        if global_settings:
            st.session_state.user_settings = global_settings
        else:
            st.session_state.user_settings = {
                "selected_categories": [],
                "custom_statements": []
            }

    # Sidebar navigation based on role
    st.sidebar.title("Digibot")
    
    # Show role indicator and logout button
    st.sidebar.success(f"Logged in as {st.session_state.user['username']} ({st.session_state.current_role})")
    if st.sidebar.button("Logout"):
        # Clear session data using new functions
        clear_session_data()
        clear_session_from_state()
        
        # Clear authentication
        st.session_state.authenticated = False
        st.session_state.current_role = None
        st.session_state.user = None
        
        # Clear remaining session state
        for key in list(st.session_state.keys()):
            if key not in ['authenticated', 'current_role', 'user']:
                del st.session_state[key]
                
        # Clear any remaining query params
        st.query_params.clear()
        st.rerun()
    
    # Initialize navigation state if not exists - simplified approach
    if 'current_nav_page' not in st.session_state:
        default_page = "User Journey" if st.session_state.current_role != "admin" else "Home"
        st.session_state.current_nav_page = default_page
        print(f"DEBUG: Initialized navigation page: {default_page}")
    else:
        print(f"DEBUG: Current navigation page: {st.session_state.current_nav_page}")
    
    # Navigation based on role
    if st.session_state.current_role == "admin":
        # Main navigation options
        nav_options = ["Home", "Self Assessment Settings", "User Journey", "Analytics", "Prompt Engineer", "User Management"]
        
        print(f"DEBUG: nav_options = {nav_options}")
        
        # Simple radio without any complex logic
        page = st.sidebar.radio(
            "Navigation",
            nav_options,
            key="admin_nav_radio"
        )
        print(f"DEBUG: Admin navigation radio selected: {page}")
        
    else:
        page = "User Journey"
    
    # Determine final page and update state
    final_page = page
    
    # Update navigation state based on widget selection
    print(f"DEBUG: Widget selected: {final_page}, Current state: {st.session_state.get('current_nav_page', 'None')}")
    
    # Update current nav page
    st.session_state.current_nav_page = final_page
    
    # Page routing based on final page
    if final_page == "User Journey":
        display_user_flow()
    elif st.session_state.current_role == "admin":
        if final_page == "Home":
            display_home_page()
        elif final_page == "Self Assessment Settings":
            display_user_settings()
        elif final_page == "Analytics":
            display_analytics()
        elif final_page == "Prompt Engineer":
            display_prompt_engineer(sample_statements)
        elif final_page == "User Management":
            display_user_management()

    # Add footer with logout button for non-admin users  
    st.markdown("---")
    
    # For non-admin users, add logout button in footer for better mobile accessibility
    if st.session_state.current_role != "admin":
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:  # Center the logout button
            if st.button("🚪 Logout", key="user_logout_footer", 
                        help="Logout from DigiBot", 
                        use_container_width=True,
                        type="secondary"):
                # Clear session data using new functions
                clear_session_data()
                clear_session_from_state()
                
                # Clear authentication
                st.session_state.authenticated = False
                st.session_state.current_role = None
                st.session_state.user = None
                
                # Clear remaining session state
                for key in list(st.session_state.keys()):
                    if key not in ['authenticated', 'current_role', 'user']:
                        del st.session_state[key]
                        
                # Clear any remaining query params
                st.query_params.clear()
                st.rerun()
    
    st.markdown("DigiBot Demo | Created with Streamlit and LangChain")
    
    print(f"DEBUG: run_app() ending normally")