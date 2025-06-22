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

def navigate_to_step(step_number):
    """Helper function to navigate to a specific step"""
    if 1 <= step_number <= 3:
        current_step = st.session_state.flow_step
        
        # If going backwards, clear relevant state
        if step_number < current_step:
            clear_state_for_backward_navigation(current_step, step_number)
        
        st.session_state.flow_step = step_number
        st.rerun()

def navigate_back_to_step(step_number):
    """Special function for explicit back navigation that clears state"""
    if 1 <= step_number <= 3:
        current_step = st.session_state.flow_step
        
        # Clear state when going backwards
        if step_number < current_step:
            clear_state_for_backward_navigation(current_step, step_number)
        
        st.session_state.flow_step = step_number
        st.rerun()

def clear_state_for_backward_navigation(from_step, to_step):
    """Clear session state when navigating backwards"""
    # If going back from Results (step 3) to Self-Assessment (step 2)
    if from_step == 3 and to_step == 2:
        # Clear quiz results and related state
        reset_quiz_session_state()
        # Also clear any completed flags that might cause auto-advancement
        if 'quiz_completed' in st.session_state:
            del st.session_state['quiz_completed']
    
    # If going back from Self-Assessment (step 2) to Profile (step 1)
    elif from_step == 2 and to_step == 1:
        # Clear quiz state but keep profile
        reset_quiz_session_state()
        # Clear enriched statements so they can be regenerated
        if 'enriched_statements' in st.session_state:
            st.session_state.enriched_statements = []
        if 'quiz_completed' in st.session_state:
            del st.session_state['quiz_completed']

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
        # Always start with empty statements - let the system generate fresh ones based on settings
        # This prevents showing old/accumulated statements and ensures consistency with current settings
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
    
    # Display step indicators with clickable navigation
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        step_num = i + 1
        with col:
            if step_num < current_step:
                # Completed step - make it clickable
                if st.button(f"✅ {step}", key=f"nav_step_{step_num}", help=f"Go back to {step}"):
                    navigate_to_step(step_num)
            elif step_num == current_step:
                # Current step
                st.markdown(f"### 🔵 {step}")
            else:
                # Future step
                st.markdown(f"### ⚪ {step}")
    
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
    
    # Reset iteration counter
    if 'current_quiz_iteration' in st.session_state:
        st.session_state.current_quiz_iteration = 0
    
    # Reset current statements
    if 'current_statements' in st.session_state:
        del st.session_state['current_statements']
