import streamlit as st
from services.enrichment_service import (
    enrich_statement_with_llm, 
    DEFAULT_PROMPT,
    BASIC_PROMPT,
    DIGCOMP_FEW_SHOT_PROMPT,
    GENERAL_FEW_SHOT_PROMPT
)
from services.metrics_service import calculate_quality_metrics
from services.db.crud._profiles import get_all_profiles, get_profile
from services.db.crud._prompts import save_prompt, get_user_prompts, delete_prompt
import json

def display_prompt_engineer(sample_statements):
    st.title("🔧 Prompt Engineer")
    
    # Initialize session state for prompts if not exists
    if 'prompts' not in st.session_state:
        # Load prompts from database
        user_prompts = get_user_prompts(st.session_state.user["id"])
        
        # If no prompts in database, initialize with default prompts
        if not user_prompts:
            st.session_state.prompts = {
                'default': DEFAULT_PROMPT,
                'basic': BASIC_PROMPT,
                'digcomp_few_shot': DIGCOMP_FEW_SHOT_PROMPT,
                'general_few_shot': GENERAL_FEW_SHOT_PROMPT
            }
        else:
            # Make sure we always have all default prompts
            if 'default' not in user_prompts:
                user_prompts['default'] = DEFAULT_PROMPT
            if 'basic' not in user_prompts:
                user_prompts['basic'] = BASIC_PROMPT
            if 'digcomp_few_shot' not in user_prompts:
                user_prompts['digcomp_few_shot'] = DIGCOMP_FEW_SHOT_PROMPT
            if 'general_few_shot' not in user_prompts:
                user_prompts['general_few_shot'] = GENERAL_FEW_SHOT_PROMPT
            st.session_state.prompts = user_prompts
    
    # Make sure all default prompts exist in prompts
    if 'default' not in st.session_state.prompts:
        st.session_state.prompts['default'] = DEFAULT_PROMPT
    if 'basic' not in st.session_state.prompts:
        st.session_state.prompts['basic'] = BASIC_PROMPT
    if 'digcomp_few_shot' not in st.session_state.prompts:
        st.session_state.prompts['digcomp_few_shot'] = DIGCOMP_FEW_SHOT_PROMPT
    if 'general_few_shot' not in st.session_state.prompts:
        st.session_state.prompts['general_few_shot'] = GENERAL_FEW_SHOT_PROMPT
    
    if 'current_prompt' not in st.session_state:
        st.session_state.current_prompt = 'default'
    
    if 'selected_profile' not in st.session_state:
        st.session_state.selected_profile = 'current'
    
    st.markdown("""
    This page allows you to experiment with different prompts for statement enrichment.
    You can create, test, and compare different prompt variations to find the most effective one.
    """)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Prompt Management")
        
        # Prompt selection or creation
        prompt_option = st.radio("Select an option:", ["Use Existing Prompt", "Create New Prompt"])
        
        if prompt_option == "Use Existing Prompt":
            selected_prompt = st.selectbox(
                "Select a prompt:",
                list(st.session_state.prompts.keys()),
                index=list(st.session_state.prompts.keys()).index(st.session_state.current_prompt)
            )
            # Update current_prompt in session state when a prompt is selected
            st.session_state.current_prompt = selected_prompt
            current_prompt = st.session_state.prompts[selected_prompt]
            
            # Display the selected prompt text
            st.text_area("Current prompt template:", value=current_prompt, height=400, disabled=True)
            
            # Add delete button for non-default prompts
            if selected_prompt != 'default' and selected_prompt != 'basic' and selected_prompt != 'digcomp_few_shot' and selected_prompt != 'general_few_shot':
                if st.button("Delete Selected Prompt"):
                    if delete_prompt(st.session_state.user["id"], selected_prompt):
                        del st.session_state.prompts[selected_prompt]
                        st.session_state.current_prompt = 'default'
                        st.success(f"Prompt '{selected_prompt}' deleted successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to delete prompt.")
        else:
            new_prompt_name = st.text_input("New prompt name:")
            current_prompt = st.text_area(
                "Enter your prompt template:",
                height=400,
                value=st.session_state.prompts[st.session_state.current_prompt]
            )
            
            if st.button("Save New Prompt") and new_prompt_name:
                if save_prompt(st.session_state.user["id"], new_prompt_name, current_prompt):
                    st.session_state.prompts[new_prompt_name] = current_prompt
                    st.session_state.current_prompt = new_prompt_name
                    st.success(f"Prompt '{new_prompt_name}' saved successfully!")
                else:
                    st.error("Failed to save prompt to database.")
    
    with col2:
        st.subheader("Available Variables")
        st.markdown("""
        Use these variables in your prompt:
        - `{context}`: User profile information
        - `{original_statement}`: The statement to enrich
        - `{length}`: Target character length
        """)
        
        # Profile selection
        st.subheader("Profile Selection")
        profile_option = st.radio("Select profile to use:", ["Current Profile", "Other Profile"])
        
        active_profile = {}
        
        if profile_option == "Current Profile":
            if not st.session_state.profile["job_role"]:
                st.warning("Your profile is incomplete. Please create your profile in the Profile Builder section.")
            else:
                active_profile = st.session_state.profile
                st.session_state.selected_profile = 'current'
        else:
            # Get all available profiles
            all_profiles = get_all_profiles()
            if not all_profiles:
                st.warning("No other profiles available.")
            else:
                profile_options = {f"{p['job_role']} ({p['user_id']})": p['user_id'] for p in all_profiles}
                selected_profile_name = st.selectbox("Select a profile:", options=list(profile_options.keys()))
                
                if selected_profile_name:
                    user_id = profile_options[selected_profile_name]
                    active_profile = get_profile(user_id)
                    st.session_state.selected_profile = user_id
        
        # Display active profile
        st.subheader("Active Profile")
        for key, value in active_profile.items():
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")
    
    # Generation Settings section
    st.subheader("Generation Settings")
    st.markdown("""
    This section allows you to configure how statements are generated and evaluated.
    """)

    col1, col2 = st.columns(2)

    with col1:
        # Toggle for evaluation mode
        evaluation_enabled = st.toggle(
            "Enable Multiple Attempts (Threshold-based Generation)", 
            value=st.session_state.get("evaluation_enabled", True)
        )
        
        # Update session state
        st.session_state.evaluation_enabled = evaluation_enabled
        
        # Explanation
        if evaluation_enabled:
            st.info("The system will generate multiple versions of the statement and select the best one based on quality thresholds.")
        else:
            st.info("The system will generate a single version of the statement without evaluation.")

    with col2:
        # Slider for max attempts (only shown if evaluation is enabled)
        if evaluation_enabled:
            max_attempts = st.slider(
                "Maximum Generation Attempts", 
                min_value=1, 
                max_value=10, 
                value=st.session_state.get("evaluation_max_attempts", 5),
                help="Maximum number of attempts to generate a statement that meets quality thresholds."
            )
            
            # Update session state
            st.session_state.evaluation_max_attempts = max_attempts
        else:
            # Set a default value when disabled
            st.session_state.evaluation_max_attempts = 1
    
    # Testing section
    st.subheader("Test Your Prompt")
    
    # Statement selection
    statement_option = st.selectbox(
        "Select a statement or choose 'Custom' to enter your own:",
        ["Custom"] + sample_statements
    )
    
    if statement_option == "Custom":
        original_statement = st.text_area("Enter your statement:", height=100)
    else:
        original_statement = statement_option
    
    statement_length = st.slider("Statement Length (characters)", 100, 300, 150)
    
    if st.button("Test Enrichment") and original_statement:
        if not active_profile:
            st.error("Please select a valid profile before testing.")
        else:
            try:
                with st.spinner("Processing..."):
                    # Create context from profile
                    context = ", ".join(
                        [f"{k.replace('_', ' ').title()}: {v}" for k, v in active_profile.items() if v])
                    
                    # Get generation settings from session state
                    evaluation_enabled = st.session_state.get("evaluation_enabled", True)
                    max_attempts = st.session_state.get("evaluation_max_attempts", 5)
                    
                    # Choose generation method based on settings
                    if evaluation_enabled:
                        # Use threshold-based generation with multiple attempts
                        from services.statement_evaluation_service import regenerate_until_threshold
                        
                        # Get proficiency level from profile or use default
                        proficiency = active_profile.get("digital_proficiency", "Intermediate")
                        
                        # Generate with multiple attempts
                        original, enriched_statement, evaluation, attempts, history = regenerate_until_threshold(
                            context=context,
                            original_statement=original_statement,
                            proficiency=proficiency,
                            statement_length=statement_length,
                            prompt_template=current_prompt,
                            max_attempts=max_attempts
                        )
                        
                        # Get metrics from the best attempt
                        metrics = history[-1]["metrics"] if history else calculate_quality_metrics(original_statement, enriched_statement)
                        
                        # Show attempt information
                        st.success(f"Statement generated after {attempts} attempt(s)")
                        
                    else:
                        # Use simple generation (single attempt)
                        enriched_statement = enrich_statement_with_llm(
                            context, 
                            original_statement, 
                            statement_length,
                            current_prompt
                        )
                        
                        # Calculate metrics
                        metrics = calculate_quality_metrics(original_statement, enriched_statement)
                    
                    # Display results
                    st.subheader("Results")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("### Original Statement")
                        st.info(original_statement)
                    
                    with col2:
                        st.markdown("### Enriched Statement")
                        st.success(enriched_statement)
                    
                    # Display metrics
                    st.subheader("Quality Metrics")
                    metrics_cols = st.columns(3)
                    
                    with metrics_cols[0]:
                        st.metric("TF-IDF Similarity", f"{metrics['cosine_tfidf']:.2f}")
                    
                    with metrics_cols[1]:
                        st.metric("Embedding Similarity", f"{metrics['cosine_embedding']:.2f}")
                    
                    with metrics_cols[2]:
                        st.metric("Reading Ease", f"{metrics['readability']['estimated_reading_ease']:.1f}")
                    
                    # Show detailed metrics
                    with st.expander("Detailed Metrics"):
                        st.json(metrics)
                    
                    # Show evaluation results if available
                    if evaluation_enabled and 'evaluation' in locals() and evaluation != "Evaluation disabled":
                        with st.expander("AI Evaluation", expanded=True):
                            st.markdown("### Statement Evaluation")
                            st.markdown(evaluation)
                            
                            # Extract and display scores if available
                            if 'history' in locals() and history:
                                scores = history[-1].get("scores", {})
                                if scores:
                                    score_cols = st.columns(4)
                                    with score_cols[0]:
                                        st.metric("Clarity", scores.get("clarity", 0))
                                    with score_cols[1]:
                                        st.metric("Relevance", scores.get("relevance_for_context", 0))
                                    with score_cols[2]:
                                        st.metric("Original Meaning", scores.get("retention_of_original_meaning", 0))
                                    with score_cols[3]:
                                        st.metric("Difficulty", scores.get("difficulty", 0))
                
            except Exception as e:
                st.error(f"Error during enrichment: {str(e)}") 