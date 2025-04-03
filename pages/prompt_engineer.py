import streamlit as st
from services.enrichment_service import enrich_statement_with_llm, DEFAULT_PROMPT
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
        
        # If no prompts in database, initialize with default
        if not user_prompts:
            st.session_state.prompts = {
                'default': DEFAULT_PROMPT
            }
        else:
            # Make sure we always have a default prompt
            if 'default' not in user_prompts:
                user_prompts['default'] = DEFAULT_PROMPT
            st.session_state.prompts = user_prompts
    
    # Make sure 'default' key exists in prompts
    if 'default' not in st.session_state.prompts:
        st.session_state.prompts['default'] = DEFAULT_PROMPT
    
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
            current_prompt = st.session_state.prompts[selected_prompt]
            
            # Display the selected prompt text
            st.text_area("Current prompt template:", value=current_prompt, height=200, disabled=True)
            
            # Add delete button for non-default prompts
            if selected_prompt != 'default':
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
                height=200,
                value=st.session_state.prompts['default']
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
                    
                    # Enrich statement
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
                    
            except Exception as e:
                st.error(f"Error during enrichment: {str(e)}") 