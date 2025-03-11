import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Import service functions
from service import (
    load_llm, 
    load_embedding_model, 
    enrich_statement_with_llm, 
    calculate_quality_metrics, 
    generate_chat_response,
    get_sample_statements
)

# Import page display functions
from pages.home import display_home_page
from pages.profile_builder import display_profile_builder
from pages.enrichment_demo import display_enrichment_demo
from pages.batch_enrichment import display_batch_enrichment
from pages.quiz import display_quiz
from pages.chatbot import display_chatbot
from pages.analytics import display_analytics
from pages.user_flow import display_user_flow
from pages.user_settings import display_user_settings

def run_app():
    # Debug information
    print("DEBUG: Starting run_app() function")
    
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = {
            "id": 1,
            "username": "demo_user",
            "role": "user"
        }
        print("DEBUG: Initialized user session state")

    if 'profile' not in st.session_state:
        st.session_state.profile = {
            "job_role": "Frontend developer",
            "job_domain": "IT Development",
            "years_experience": 4,
            "digital_proficiency": "Intermediate",
            "primary_tasks": "Working with Figma, creating responsive SCSS styles and creating components in Angular"
        }

    if 'enriched_statements' not in st.session_state:
        st.session_state.enriched_statements = []
        
    if 'quiz_results' not in st.session_state:
        st.session_state.quiz_results = {"original": 0, "enriched": 0}

    # Add detailed quiz results structure
    if 'detailed_quiz_results' not in st.session_state:
        st.session_state.detailed_quiz_results = {
            "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
        }

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Initialize user settings if not exists
    if 'user_settings' not in st.session_state:
        st.session_state.user_settings = {
            "selected_categories": [],
            "custom_statements": [],
            "max_statements_per_quiz": 5
        }

    # Get sample statements
    sample_statements = get_sample_statements()

    # Sidebar navigation
    st.sidebar.title("DigiBot Demo")
    page = st.sidebar.radio(
        "Navigation",
        ["Home", "User Journey", "Profile Builder", "User Settings", "Enrichment Demo", "Batch Enrichment", "Quiz", "Chatbot", "Analytics"]
    )

    # Home page
    if page == "Home":
        display_home_page()

    # User Journey page
    elif page == "User Journey":
        display_user_flow()

    # Profile Builder page
    elif page == "Profile Builder":
        display_profile_builder()

    # User Settings page
    elif page == "User Settings":
        display_user_settings()

    # Enrichment Demo page
    elif page == "Enrichment Demo":
        display_enrichment_demo(sample_statements)

    # Batch Enrichment page
    elif page == "Batch Enrichment":
        display_batch_enrichment(sample_statements)
    
    # Quiz page
    elif page == "Quiz":
        display_quiz()

    # Chatbot page
    elif page == "Chatbot":
        display_chatbot()

    # Analytics page
    elif page == "Analytics":
        display_analytics()

    # Add footer
    st.markdown("---")
    st.markdown("DigiBot Demo | Created with Streamlit and LangChain")