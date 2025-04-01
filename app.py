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
    get_user_statements,
    save_quiz_results,
    get_quiz_results,
    save_profile,
    get_profile,
    get_global_settings,
    save_global_settings,
    get_user_by_id,
    verify_session_token
)

# Import page display functions
from pages.home import display_home_page
from pages.profile_builder import display_profile_builder
from pages.enrichment_demo import display_enrichment_demo
from pages.batch_enrichment import display_batch_enrichment
from pages.quiz import display_quiz
from pages.chatbot import display_chatbot
from pages.analytics import display_analytics
from pages.user_page.user_flow import display_user_flow
from pages.user_settings import display_user_settings
from pages.prompt_engineer import display_prompt_engineer

# Import database connection and models
from services.db.connection import get_database_connection
from services.db.models import UserSession

def verify_session_token(user_id, token):
    """Verify that the session token is valid for the given user_id"""
    # Здесь должна быть логика проверки токена в базе данных
    # Например, проверка в таблице sessions, где хранятся активные сессии
    db = get_database_connection()
    if not db:
        return False
    
    session = db["Session"]()
    try:
        # Проверяем токен в базе данных
        session_record = session.query(UserSession).filter_by(
            user_id=user_id, 
            token=token,
            expired=False
        ).first()
        
        if session_record:
            # Проверяем, не истек ли срок действия токена
            if session_record.expires_at > datetime.datetime.utcnow():
                return True
            else:
                # Помечаем токен как истекший
                session_record.expired = True
                session.commit()
        return False
    except Exception as e:
        print(f"Error verifying session token: {e}")
        return False
    finally:
        session.close()

def run_app():
    # Hide default sidebar navigation
    st.markdown("""
        <style>
        [data-testid="stSidebarNav"] {
            display: none;
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

    # Try to restore session from query params if not authenticated
    if not st.session_state.authenticated:
        try:
            # Get user_id and session_token from query params
            user_id = st.query_params.get('user_id')
            session_token = st.query_params.get('session_token')
            
            if user_id and session_token:
                # Verify session token is valid for this user
                if verify_session_token(int(user_id), session_token):
                    # Try to get user from database
                    user = get_user_by_id(int(user_id))
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user
                        st.session_state.current_role = user["role"]
                else:
                    # Invalid session token, clear query params
                    st.query_params.clear()
        except Exception as e:
            print(f"Error restoring session: {e}")
            # Clear query params on error
            st.query_params.clear()

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
        user_statements = get_user_statements(st.session_state.user["id"])
        if user_statements:
            st.session_state.enriched_statements = user_statements
        else:
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
                "custom_statements": [],
                "max_statements_per_quiz": 5
            }

    # Sidebar navigation based on role
    st.sidebar.title("Digibot")
    
    # Show role indicator and logout button
    st.sidebar.success(f"Logged in as {st.session_state.user['username']} ({st.session_state.current_role})")
    if st.sidebar.button("Logout"):
        # Clear authentication first
        st.session_state.authenticated = False
        st.session_state.current_role = None
        st.session_state.user = None
        
        # Clear remaining session state
        for key in list(st.session_state.keys()):
            if key not in ['authenticated', 'current_role', 'user']:
                del st.session_state[key]
                
        # Force redirect to auth page
        st.query_params.clear()
        st.rerun()
    
    # Navigation based on role
    if st.session_state.current_role == "admin":
        page = st.sidebar.radio(
            "Navigation",
            ["Home", "User Settings", "User Journey", "Profile Builder", 
             "Enrichment Demo", "Batch Enrichment", "Quiz", "Chatbot", "Analytics", "Prompt Engineer"]
        )
    else:
        page = "User Journey"
    
    # Page routing
    if page == "User Journey":
        display_user_flow()
    elif st.session_state.current_role == "admin":
        if page == "Home":
            display_home_page()
        elif page == "User Settings":
            display_user_settings()
        elif page == "Profile Builder":
            display_profile_builder()
        elif page == "Enrichment Demo":
            display_enrichment_demo(sample_statements)
        elif page == "Batch Enrichment":
            display_batch_enrichment(sample_statements)
        elif page == "Quiz":
            display_quiz()
        elif page == "Chatbot":
            display_chatbot()
        elif page == "Analytics":
            display_analytics()
        elif page == "Prompt Engineer":
            display_prompt_engineer(sample_statements)

    # Add footer
    st.markdown("---")
    st.markdown("DigiBot Demo | Created with Streamlit and LangChain")