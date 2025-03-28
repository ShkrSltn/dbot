import streamlit as st
from services.enrichment_service import enrich_statement_with_llm, DEFAULT_PROMPT
from services.metrics_service import calculate_quality_metrics
import json

def display_prompt_engineer(sample_statements):
    st.title("🔧 Prompt Engineer")
    
    if not st.session_state.profile["job_role"]:
        st.warning("Please create your profile first in the Profile Builder section.")
        st.stop()
        
    # Initialize session state for prompts if not exists
    if 'prompts' not in st.session_state:
        st.session_state.prompts = {
            'default': DEFAULT_PROMPT
        }
    
    if 'current_prompt' not in st.session_state:
        st.session_state.current_prompt = 'default'
    
    st.markdown("""
    This page allows you to experiment with different prompts for statement enrichment.
    You can create, test, and compare different prompt variations to find the most effective one.
    """)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Prompt management
        st.subheader("Prompt Management")
        
        # Prompt selection or creation
        prompt_action = st.radio("Select action:", ["Use existing prompt", "Create new prompt"])
        
        if prompt_action == "Use existing prompt":
            selected_prompt = st.selectbox(
                "Select a prompt template:",
                options=list(st.session_state.prompts.keys())
            )
            current_prompt = st.session_state.prompts[selected_prompt]
        else:
            new_prompt_name = st.text_input("New prompt name:")
            current_prompt = st.text_area(
                "Enter your prompt template:",
                height=200,
                value=st.session_state.prompts['default']
            )
            
            if st.button("Save New Prompt") and new_prompt_name:
                st.session_state.prompts[new_prompt_name] = current_prompt
                st.success(f"Prompt '{new_prompt_name}' saved successfully!")
                st.session_state.current_prompt = new_prompt_name
    
    with col2:
        st.subheader("Available Variables")
        st.markdown("""
        Use these variables in your prompt:
        - `{context}`: User profile information
        - `{original_statement}`: The statement to enrich
        - `{length}`: Target character length
        """)
        
        # Display current profile
        st.subheader("Your Profile")
        for key, value in st.session_state.profile.items():
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
        try:
            with st.spinner("Processing..."):
                # Create context from profile
                context = ", ".join(
                    [f"{k.replace('_', ' ').title()}: {v}" for k, v in st.session_state.profile.items() if v])
                
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