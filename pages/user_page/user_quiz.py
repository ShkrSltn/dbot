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
        
        # Enrich statements
        with st.spinner("Generating sample statements..."):
            for statement in sample_statements:
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
    # Custom quiz implementation for the flow
    # Select a random statement that hasn't been shown in the quiz yet
    if 'quiz_shown_indices' not in st.session_state:
        st.session_state.quiz_shown_indices = []
        
    available_indices = [i for i in range(len(st.session_state.enriched_statements)) 
                        if i not in st.session_state.quiz_shown_indices]
    
    if not available_indices:
        # All statements have been shown, move to results
        st.session_state.flow_step = 3
        st.rerun()
    else:
        # Select a random statement
        if 'current_statement_idx' not in st.session_state:
            st.session_state.current_statement_idx = np.random.choice(available_indices)
        
        statement_idx = st.session_state.current_statement_idx
        statement_pair = st.session_state.enriched_statements[statement_idx]
        
        # Create a unique key for this quiz iteration to ensure form elements reset
        if 'current_quiz_iteration' not in st.session_state:
            st.session_state.current_quiz_iteration = 0
        
        quiz_iteration_key = f"quiz_iteration_{st.session_state.current_quiz_iteration}"
        
        # Always set original on the left (A) and enriched on the right (B)
        first_is_original = True
        st.session_state.first_is_original = first_is_original
            
        first_statement = statement_pair["original"]
        second_statement = statement_pair["enriched"]
            
        st.markdown("Compare these two statements and select your preferences:")
        
        # Display the statements side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### A")
            st.info(first_statement)
            
        with col2:
            st.markdown("### B")
            st.info(second_statement)
            
        # Add a divider
        st.markdown("---")
        
        # Create the detailed preference form
        st.markdown("### Your Preference")
        
        # Define the criteria questions
        criteria = {
            "understand": "Which statement is easier to understand?",
            "read": "Which statement is easier to read?",
            "detail": "Which statement offers greater detail?",
            "profession": "Which statement fits your profession?",
            "assessment": "Which statement is helpful for a self-assessment?"
        }
        
        # Create a form for all criteria
        with st.form(key=f"flow_preference_form_{quiz_iteration_key}"):
            # Create sliders for each criterion
            for key, question in criteria.items():
                # Use a unique key for each slider that includes the iteration
                slider_key = f"slider_{key}_{quiz_iteration_key}"
                
                # Create the slider without setting default value in session state
                st.select_slider(
                    question,
                    options=["Completely Prefer A", "Somewhat Prefer A", "Neither", "Somewhat Prefer B", "Completely Prefer B"],
                    value="Completely Prefer A",
                    key=slider_key
                )
            
            # Progress indicator
            total_statements = min(10, len(st.session_state.enriched_statements))  # Limit to 5 statements max
            completed = len(st.session_state.quiz_shown_indices)
            progress_percentage = completed / total_statements * 100
            
            st.progress(progress_percentage / 100, f"{progress_percentage:.0f}% ({completed}/{total_statements})")
            
            # Submit button
            submitted = st.form_submit_button("Submit and Continue")
            
        if submitted:
            # Collect responses from session state after form submission
            responses = {}
            for key in criteria.keys():
                slider_key = f"slider_{key}_{quiz_iteration_key}"
                responses[key] = st.session_state[slider_key]
            
            # Handle the submission
            handle_quiz_submission(statement_idx, responses, first_is_original)
            
            # Reset for next question
            st.session_state.current_quiz_iteration += 1
            st.session_state.pop('current_statement_idx', None)
            st.session_state.pop('first_is_original', None)

def handle_quiz_submission(statement_idx, responses, first_is_original):
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
    
    # Update overall quiz results based on the average score
    # Instead of incrementing counters, we'll track each statement's preference
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
    st.session_state.quiz_shown_indices.append(statement_idx)
    
    # Check if we've shown enough statements (limit to max from settings)
    max_statements = 5  # Default
    if 'user_settings' in st.session_state and 'max_statements_per_quiz' in st.session_state.user_settings:
        max_statements = st.session_state.user_settings["max_statements_per_quiz"]
    
    # Determine if this is the final submission for this quiz attempt
    is_final = len(st.session_state.quiz_shown_indices) >= min(max_statements, len(st.session_state.enriched_statements))
    
    # Calculate the final counts based on all statement preferences
    original_count = st.session_state.statement_preferences.count("original")
    enriched_count = st.session_state.statement_preferences.count("enriched")
    neither_count = st.session_state.statement_preferences.count("neither")
    
    # Update the quiz results with the correct counts
    st.session_state.quiz_results = {
        "original": original_count,
        "enriched": enriched_count,
        "neither": neither_count
    }
    
    # Save quiz results to database
    save_quiz_results(
        st.session_state.user["id"],
        original_count,
        enriched_count,
        neither_count,
        st.session_state.detailed_quiz_results,
        is_final=is_final
    )
    
    # If this is the final submission, update the list of previous results
    if is_final:
        from services.db.crud._quiz import get_quiz_results_list
        st.session_state.previous_quiz_results = get_quiz_results_list(st.session_state.user["id"])
        st.session_state.has_previous_results = True
        st.session_state.flow_step = 3
    
    # Rerun to show the next question or move to results
    st.rerun()
