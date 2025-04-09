import streamlit as st
from pages.user_page.user_profile import display_profile_step
from pages.user_page.user_quiz import display_quiz_step
from pages.user_page.user_results import display_results_step
from services.db.crud._profiles import get_profile
from services.db.crud._quiz import get_quiz_results_list
from services.db.crud._statements import get_user_statements

# Main flow controller
def display_user_flow():
    st.title("🚶 User Journey")
    
    initialize_session_state()
    display_progress_bar()
    
    # Handle different steps of the flow
    if st.session_state.flow_step == 1:
        display_profile_step()
    elif st.session_state.flow_step == 2:
        display_quiz_step()
    elif st.session_state.flow_step == 3:
        display_results_step()

# Session state initialization
def initialize_session_state():
    # Initialize flow state if not exists
    if 'flow_step' not in st.session_state:
        # Check if user has already completed a quiz before
        db_quiz_results_list = get_quiz_results_list(st.session_state.user["id"])
        if db_quiz_results_list and len(db_quiz_results_list) > 0:
            # User has previous quiz results, set flow step to results page
            st.session_state.flow_step = 3
            st.session_state.has_previous_results = True
            st.session_state.previous_quiz_results = db_quiz_results_list
        else:
            # No previous results, start from the beginning
            st.session_state.flow_step = 1
            st.session_state.has_previous_results = False
    
    # Always check for previous results, even if flow_step is already set
    if 'has_previous_results' not in st.session_state or 'previous_quiz_results' not in st.session_state:
        db_quiz_results_list = get_quiz_results_list(st.session_state.user["id"])
        st.session_state.has_previous_results = bool(db_quiz_results_list and len(db_quiz_results_list) > 0)
        if st.session_state.has_previous_results:
            st.session_state.previous_quiz_results = db_quiz_results_list
    
    # Initialize statement preferences tracking
    if 'statement_preferences' not in st.session_state:
        st.session_state.statement_preferences = []
    
    # Try to load existing profile from database
    if 'profile' not in st.session_state:
        db_profile = get_profile(st.session_state.user["id"])
        if db_profile:
            st.session_state.profile = db_profile
        else:
            st.session_state.profile = {}
    
    # Initialize quiz_results if not exists
    if 'quiz_results' not in st.session_state:
        st.session_state.quiz_results = {"original": 0, "enriched": 0, "neither": 0}
    
    # Initialize detailed_quiz_results if not exists
    if 'detailed_quiz_results' not in st.session_state:
        st.session_state.detailed_quiz_results = {
            "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
        }
    
    # Load user statements from database
    if 'enriched_statements' not in st.session_state:
        user_statements = get_user_statements(st.session_state.user["id"])
        if user_statements:
            st.session_state.enriched_statements = user_statements
        else:
            st.session_state.enriched_statements = []
            
    # Initialize quiz_shown_indices if not exists
    if 'quiz_shown_indices' not in st.session_state:
        st.session_state.quiz_shown_indices = []

# Progress bar and step indicators
def display_progress_bar():
    steps = ["Profile", "Self-Assessment", "Results"]
    current_step = st.session_state.flow_step
    
    # Calculate progress percentage
    progress = (current_step - 1) / (len(steps) - 1) if len(steps) > 1 else 1.0
    
    # Display progress bar and step indicator
    st.progress(progress)
    
    # Display step indicators
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        step_num = i + 1
        if step_num < current_step:
            col.markdown(f"### ✅ {step}")
        elif step_num == current_step:
            col.markdown(f"### 🔵 {step}")
        else:
            col.markdown(f"### ⚪ {step}")
    
    st.markdown("---")

def reset_quiz_session_state():
    """Reset all quiz-related session state variables"""
    # Reset quiz results
    st.session_state.quiz_results = {"original": 0, "enriched": 0, "neither": 0}
    
    # Reset statement preferences
    st.session_state.statement_preferences = []
    
    # Reset detailed quiz results
    st.session_state.detailed_quiz_results = {
        "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
        "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
        "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
        "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
        "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
    }
    
    # Reset shown indices
    st.session_state.quiz_shown_indices = []
