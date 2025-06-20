import streamlit as st
import numpy as np
from services.statement_service import get_statements_from_settings, get_category_for_statement
from services.enrichment_service import enrich_statement_with_llm
from services.metrics_service import calculate_quality_metrics
from services.db.crud._quiz import save_quiz_results

def display_quiz_step():
    st.subheader("Step 2: Statement Preference Self-Assessment")
    
    # Check if we have enriched statements
    if len(st.session_state.get('enriched_statements', [])) < 1:
        handle_empty_statements()
    else:
        display_quiz_interface()

def handle_empty_statements():
    # Generate some sample enriched statements for testing
    if st.button("Let's start the self-assessment"):
        # Get statements based on user settings
        sample_statements = get_statements_from_settings()
        
        # Limit to max statements per quiz from settings
        max_statements = get_max_statements_setting()
        
        # Take only the first max_statements
        sample_statements = sample_statements[:max_statements]
        
        # Create context from profile
        context = ", ".join(
            [f"{k.replace('_', ' ').title()}: {v}" for k, v in st.session_state.profile.items() if v])
        
        # Enrich statements
        with st.spinner("Generating sample statements..."):
            for statement in sample_statements:
                # Get category and subcategory for the statement
                category, subcategory = get_category_for_statement(statement)
                
                enriched = enrich_statement_with_llm(context, statement, 150)
                metrics = calculate_quality_metrics(statement, enriched)
                
                if 'enriched_statements' not in st.session_state:
                    st.session_state.enriched_statements = []
                
                st.session_state.enriched_statements.append({
                    "original": statement,
                    "enriched": enriched,
                    "metrics": metrics,
                    "category": category,
                    "subcategory": subcategory
                })
        
        st.success(f"Generated {len(sample_statements)} statements! You can now take the self-assessment.")
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
            
            # Create sliders for each criterion for this statement pair
            st.markdown("#### Your Preference")
            for key, question in criteria.items():
                # Use a unique key for each slider that includes the statement index
                slider_key = f"slider_{key}_{statement_idx}_{quiz_iteration_key}"
                
                st.select_slider(
                    question,
                    options=["Completely Prefer A", "Somewhat Prefer A", "Neither", "Somewhat Prefer B", "Completely Prefer B"],
                    value=None,
                    key=slider_key
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
        # Process all responses
        for statement_idx in st.session_state.current_statements:
            # Collect responses for this statement
            responses = {}
            for key in criteria.keys():
                slider_key = f"slider_{key}_{statement_idx}_{quiz_iteration_key}"
                responses[key] = st.session_state[slider_key]
            
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
    
    # Process the responses
    for key, response in responses.items():
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
