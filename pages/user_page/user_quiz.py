import streamlit as st
import numpy as np
from services.statement_service import get_statements_from_settings
from services.enrichment_service import enrich_statement_with_llm
from services.metrics_service import calculate_quality_metrics
from services.db.crud._quiz import save_quiz_results

def display_quiz_step():
    st.subheader("Step 2: Statement Preference Quiz")
    
    # Check if we have enriched statements
    if len(st.session_state.get('enriched_statements', [])) < 1:
        handle_empty_statements()
    else:
        display_quiz_interface()

def handle_empty_statements():
    # Generate some sample enriched statements for testing
    if st.button("Let's start the quiz"):
        # Get statements based on user settings
        sample_statements = get_statements_from_settings()
        
        # Limit to max statements per quiz from settings
        max_statements = get_max_statements_setting()
        
        # Take only the first max_statements
        sample_statements = sample_statements[:max_statements]
        
        # Create context from profile
        context = ", ".join(
            [f"{k.replace('_', ' ').title()}: {v}" for k, v in st.session_state.profile.items() if v])
        
        # Get generation settings from global settings
        from services.db.crud._settings import get_global_settings
        global_settings = get_global_settings("user_settings")
        
        evaluation_enabled = global_settings.get("evaluation_enabled", True) if global_settings else True
        max_attempts = global_settings.get("evaluation_max_attempts", 5) if global_settings else 5
        
        # Enrich statements
        with st.spinner("Generating sample statements..."):
            for statement in sample_statements:
                # Choose generation method based on settings
                if evaluation_enabled:
                    # Use threshold-based generation with multiple attempts
                    from services.statement_evaluation_service import regenerate_until_threshold
                    
                    # Get proficiency level from profile or use default
                    proficiency = st.session_state.profile.get("digital_proficiency", "Intermediate")
                    if isinstance(proficiency, int):
                        # Convert numeric proficiency to string
                        proficiency_map = {
                            1: "Beginner",
                            2: "Basic",
                            3: "Intermediate", 
                            4: "Advanced",
                            5: "Expert"
                        }
                        proficiency = proficiency_map.get(proficiency, "Intermediate")
                    
                    # Generate with multiple attempts
                    _, enriched, _, _, history = regenerate_until_threshold(
                        context=context,
                        original_statement=statement,
                        proficiency=proficiency,
                        statement_length=150,
                        max_attempts=max_attempts
                    )
                    
                    # Get metrics from the best attempt
                    metrics = history[-1]["metrics"] if history else calculate_quality_metrics(statement, enriched)
                else:
                    # Use simple generation (single attempt)
                    enriched = enrich_statement_with_llm(context, statement, 150)
                    metrics = calculate_quality_metrics(statement, enriched)
                
                if 'enriched_statements' not in st.session_state:
                    st.session_state.enriched_statements = []
                
                st.session_state.enriched_statements.append({
                    "original": statement,
                    "enriched": enriched,
                    "metrics": metrics
                })
        
        st.success(f"Generated {len(sample_statements)} statements! You can now take the quiz.")
        st.rerun()

def get_max_statements_setting():
    # Default max statements
    max_statements = 3
    if 'user_settings' in st.session_state and 'max_statements_per_quiz' in st.session_state.user_settings:
        max_statements = st.session_state.user_settings["max_statements_per_quiz"]
    return max_statements

def display_quiz_interface():
    # Show all statements at once instead of one by one
    if 'quiz_shown_indices' not in st.session_state:
        st.session_state.quiz_shown_indices = []
    
    # Get max statements from settings
    max_statements = get_max_statements_setting()
    
    # Determine how many statements to show (limited by max_statements and available statements)
    total_statements = min(max_statements, len(st.session_state.enriched_statements))
    
    # If all statements have been shown, move to results
    if len(st.session_state.quiz_shown_indices) >= total_statements:
        st.session_state.flow_step = 3
        st.rerun()
    
    # Create a unique key for this quiz iteration
    if 'current_quiz_iteration' not in st.session_state:
        st.session_state.current_quiz_iteration = 0
    
    quiz_iteration_key = f"quiz_iteration_{st.session_state.current_quiz_iteration}"
    
    # Define the criteria questions
    criteria = {
        "understand": "Which statement is easier to understand?",
        "read": "Which statement is easier to read?",
        "detail": "Which statement offers greater detail?",
        "profession": "Which statement fits your profession?",
        "assessment": "Which statement is helpful for a self-assessment?"
    }
    
    # Create a form for all statements
    with st.form(key=f"flow_preference_form_{quiz_iteration_key}"):
        st.markdown("### Compare these statements and select your preferences")
        
        # Get available statements that haven't been shown yet
        available_indices = [i for i in range(len(st.session_state.enriched_statements)) 
                            if i not in st.session_state.quiz_shown_indices]
        
        # Select statements to show in this quiz
        statements_to_show = available_indices[:total_statements - len(st.session_state.quiz_shown_indices)]
        
        # Store the statements being shown in this quiz
        if 'current_statements' not in st.session_state:
            st.session_state.current_statements = statements_to_show
        
        # Display each statement pair with its own set of questions
        for i, statement_idx in enumerate(st.session_state.current_statements):
            statement_pair = st.session_state.enriched_statements[statement_idx]
            
            # Always set original on the left (A) and enriched on the right (B)
            first_is_original = True
            
            first_statement = statement_pair["original"]
            second_statement = statement_pair["enriched"]
            
            st.markdown(f"## Statement Pair {i+1}")
            
            # Display the statements side by side
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### A")
                st.info(first_statement)
                
            with col2:
                st.markdown("### B")
                st.info(second_statement)
            
            # Create radio buttons for each criterion for this statement pair
            st.markdown("#### Your Preference")
            
            # Add custom CSS to style radio buttons and add borders
            st.markdown("""
            <style>
                div[data-testid="stRadio"] {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    margin-bottom: 15px;
                    width: 100%;
                }
                div[data-testid="stRadio"] > div {
                    display: flex;
                    justify-content: space-between;
                    width: 100%;
                }
                div[data-testid="stRadio"] > div > label {
                    margin: 0 5px;
                }
                
                /* Media query for mobile devices */
                @media (max-width: 768px) {
                    div[data-testid="stRadio"] > div {
                        flex-direction: column;
                    }
                    div[data-testid="stRadio"] > div > label {
                        margin: 5px 0;
                    }
                }
            </style>
            """, unsafe_allow_html=True)
            
            for key, question in criteria.items():
                # Use a unique key for each radio button that includes the statement index
                radio_key = f"radio_{key}_{statement_idx}_{quiz_iteration_key}"
                
                # Determine horizontal or vertical layout based on screen width
                st.radio(
                    question,
                    options=["Completely Prefer A", "Somewhat Prefer A", "Neither", "Somewhat Prefer B", "Completely Prefer B"],
                    key=radio_key,
                    horizontal=True,  # CSS медиа-запрос переопределит это для мобильных
                    index=None  # This makes no option selected by default
                )
            
            # Add a divider between statement pairs
            if i < len(st.session_state.current_statements) - 1:
                st.markdown("---")
        
        # Progress indicator
        completed = len(st.session_state.quiz_shown_indices)
        progress_percentage = completed / total_statements * 100
        
        st.progress(progress_percentage / 100, f"{progress_percentage:.0f}% ({completed}/{total_statements})")
        
        # Submit button for all statements
        submitted = st.form_submit_button("Submit All Responses")
        
    if submitted:
        # Validate that all questions have been answered
        all_answered = True
        unanswered_questions = []
        
        for statement_idx in st.session_state.current_statements:
            for key in criteria.keys():
                radio_key = f"radio_{key}_{statement_idx}_{quiz_iteration_key}"
                if radio_key not in st.session_state or st.session_state[radio_key] is None:
                    all_answered = False
                    unanswered_questions.append(f"Statement Pair {st.session_state.current_statements.index(statement_idx)+1}: {criteria[key]}")
        
        if not all_answered:
            st.error("Please answer all questions before submitting:")
            for question in unanswered_questions:
                st.warning(question)
            return
            
        # Process all responses
        for statement_idx in st.session_state.current_statements:
            # Collect responses for this statement
            responses = {}
            for key in criteria.keys():
                radio_key = f"radio_{key}_{statement_idx}_{quiz_iteration_key}"
                responses[key] = st.session_state[radio_key]
            
            # Handle the submission for this statement
            handle_quiz_submission(statement_idx, responses, first_is_original=True)
        
        # Reset for next batch of questions if needed
        st.session_state.current_quiz_iteration += 1
        st.session_state.pop('current_statements', None)
        
        # Check if we've completed all statements
        if len(st.session_state.quiz_shown_indices) >= total_statements:
            st.session_state.flow_step = 3
        
        st.rerun()

def handle_quiz_submission(statement_idx, responses, first_is_original):
    # Initialize detailed_quiz_results if not exists
    if 'detailed_quiz_results' not in st.session_state:
        st.session_state.detailed_quiz_results = {
            "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
        }
    
    # Get current quiz iteration
    current_quiz_iteration = st.session_state.current_quiz_iteration
    quiz_iteration_key = f"quiz_iteration_{current_quiz_iteration}"
    
    # Validate responses for completeness and consistency
    if None in responses.values() or "" in responses.values():
        st.error(f"Please complete all questions for Statement Pair {statement_idx+1}")
        return False
    
    # Check for inconsistent responses (optional validation)
    preference_mapping = {
        "Completely Prefer A": 2 if first_is_original else -2,
        "Somewhat Prefer A": 1 if first_is_original else -1,
        "Neither": 0,
        "Somewhat Prefer B": -1 if first_is_original else 1,
        "Completely Prefer B": -2 if first_is_original else 2
    }
    
    preference_scores = [preference_mapping[response] for response in responses.values()]
    
    # Check if responses are highly inconsistent (e.g., some strongly prefer A while others strongly prefer B)
    max_score = max(preference_scores)
    min_score = min(preference_scores)
    if max_score >= 2 and min_score <= -2:
        # This is just a warning, not blocking submission
        st.warning(f"Your responses for Statement Pair {statement_idx+1} seem inconsistent. Please review if needed.")
    
    # Process the responses
    for key, response in responses.items():
        # Update the key to match the new radio button keys
        radio_key = f"radio_{key}_{statement_idx}_{quiz_iteration_key}"
        response = st.session_state[radio_key]
        
        # Map responses to the detailed quiz results structure
        if response == "Completely Prefer A":
            if first_is_original:
                st.session_state.detailed_quiz_results[key]["completely_prefer_original"] += 1
            else:
                st.session_state.detailed_quiz_results[key]["completely_prefer_enriched"] += 1
        elif response == "Somewhat Prefer A":
            if first_is_original:
                st.session_state.detailed_quiz_results[key]["somewhat_prefer_original"] += 1
            else:
                st.session_state.detailed_quiz_results[key]["somewhat_prefer_enriched"] += 1
        elif response == "Neither":
            st.session_state.detailed_quiz_results[key]["neither"] += 1
        elif response == "Somewhat Prefer B":
            if first_is_original:
                st.session_state.detailed_quiz_results[key]["somewhat_prefer_enriched"] += 1
            else:
                st.session_state.detailed_quiz_results[key]["somewhat_prefer_original"] += 1
        elif response == "Completely Prefer B":
            if first_is_original:
                st.session_state.detailed_quiz_results[key]["completely_prefer_enriched"] += 1
            else:
                st.session_state.detailed_quiz_results[key]["completely_prefer_original"] += 1
    
    # Calculate overall preference based on average of all criteria
    preference_mapping = {
        "Completely Prefer A": 2 if first_is_original else -2,
        "Somewhat Prefer A": 1 if first_is_original else -1,
        "Neither": 0,
        "Somewhat Prefer B": -1 if first_is_original else 1,
        "Completely Prefer B": -2 if first_is_original else 2
    }
    
    preference_scores = [preference_mapping[response] for response in responses.values()]
    average_score = sum(preference_scores) / len(preference_scores)
    
    # Initialize statement_preferences if not exists
    if 'statement_preferences' not in st.session_state:
        st.session_state.statement_preferences = []
    
    # Store the preference for this statement
    if average_score > 0.1:  # Using a small threshold to avoid floating point issues
        preference = "original"
    elif average_score < -0.1:  # Using a small threshold to avoid floating point issues
        preference = "enriched"
    else:
        # If score is close to 0, mark as "neither" instead of randomly assigning
        preference = "neither"
    
    # Add this statement's preference to our tracking list
    st.session_state.statement_preferences.append(preference)
    
    # Add to shown indices
    if statement_idx not in st.session_state.quiz_shown_indices:
        st.session_state.quiz_shown_indices.append(statement_idx)
    
    # Check if we've shown enough statements (limit to max from settings)
    max_statements = get_max_statements_setting()
    
    # Determine if this is the final submission for this quiz attempt
    is_final = len(st.session_state.quiz_shown_indices) >= min(max_statements, len(st.session_state.enriched_statements))
    
    # Calculate the final counts based on all statement preferences
    original_count = st.session_state.statement_preferences.count("original")
    enriched_count = st.session_state.statement_preferences.count("enriched")
    neither_count = st.session_state.statement_preferences.count("neither")
    
    # Initialize quiz_results if not exists
    if 'quiz_results' not in st.session_state:
        st.session_state.quiz_results = {"original": 0, "enriched": 0, "neither": 0}
    
    # Update the quiz results with the correct counts
    st.session_state.quiz_results = {
        "original": original_count,
        "enriched": enriched_count,
        "neither": neither_count
    }
    
    # Save quiz results to database only if this is the final submission
    if is_final:
        save_quiz_results(
            st.session_state.user["id"],
            original_count,
            enriched_count,
            neither_count,
            st.session_state.detailed_quiz_results,
            is_final=is_final
        )
        
        # Update the list of previous results
        from services.db.crud._quiz import get_quiz_results_list
        st.session_state.previous_quiz_results = get_quiz_results_list(st.session_state.user["id"])
        st.session_state.has_previous_results = True
        st.session_state.flow_step = 3
    
    # No rerun here - let the calling function handle it
    return is_final
