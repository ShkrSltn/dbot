import streamlit as st
from services.enrichment_service import enrich_statement_with_llm
from services.metrics_service import calculate_quality_metrics
from services.statement_service import get_statements_from_settings, get_category_for_statement
from services.db.crud._statements import save_statement

def display_batch_enrichment(sample_statements):
    st.title("🔄 Batch Enrichment")
    
    if not st.session_state.profile["job_role"]:
        st.warning("Please create your profile first in the Profile Builder section.")
        st.stop()
        
    st.markdown("""
    Select multiple statements to enrich at once or add your own custom statements.
    """)
    
    # Get statements based on user settings
    available_statements = get_statements_from_settings()
    
    # Create multiselect for available statements
    selected_samples = st.multiselect(
        "Select statements to enrich:",
        available_statements,
        default=[]
    )
    
    # Option to add custom statements
    st.subheader("Add Custom Statements")
    
    # Initialize custom statements list if not exists
    if 'custom_statements' not in st.session_state:
        st.session_state.custom_statements = [""]
        
    # Display all custom statement inputs
    custom_statements = []
    for i, statement in enumerate(st.session_state.custom_statements):
        col1, col2 = st.columns([5, 1])
        with col1:
            custom_statement = st.text_input(f"Custom statement #{i+1}", value=statement, key=f"custom_{i}")
            if custom_statement:
                custom_statements.append(custom_statement)
        with col2:
            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.custom_statements.pop(i)
                st.rerun()
    
    # Add button for new custom statement
    if st.button("Add Another Custom Statement"):
        st.session_state.custom_statements.append("")
        st.rerun()
        
    # Combine selected sample statements and custom statements
    all_statements = selected_samples + custom_statements
    
    # Statement length slider
    statement_length = st.slider("Statement Length (characters)", 100, 300, 150, key="batch_length")
    
    # Process button
    if st.button("Process All Statements") and all_statements:
        with st.spinner("Processing statements..."):
            # Create context from profile
            context = ", ".join(
                [f"{k.replace('_', ' ').title()}: {v}" for k, v in st.session_state.profile.items() if v])
            
            progress_bar = st.progress(0)
            
            # Process each statement
            for i, statement in enumerate(all_statements):
                try:
                    # Update progress
                    progress = (i + 1) / len(all_statements)
                    progress_bar.progress(progress)
                    
                    # Get category and subcategory for the statement
                    category, subcategory = get_category_for_statement(statement)
                    
                    # Enrich statement
                    enriched_statement = enrich_statement_with_llm(context, statement, statement_length)
                    
                    # Calculate metrics
                    metrics = calculate_quality_metrics(statement, enriched_statement)
                    
                    # Save to session state with category and subcategory
                    st.session_state.enriched_statements.append({
                        "original": statement,
                        "enriched": enriched_statement,
                        "metrics": metrics,
                        "category": category,
                        "subcategory": subcategory
                    })
                    
                    # Save to database
                    statement_id = save_statement(
                        st.session_state.user["id"],
                        statement,
                        enriched_statement,
                        metrics
                    )
                    
                    if statement_id:
                        print(f"Statement saved with ID: {statement_id}")
                    else:
                        print("Failed to save statement")
                    
                except Exception as e:
                    st.error(f"Error processing statement '{statement[:30]}...': {str(e)}")
            
            st.success(f"Processed {len(all_statements)} statements successfully!")
            
        # Display summary
        st.subheader("Summary of Processed Statements")
        
        for i, item in enumerate(st.session_state.enriched_statements[-len(all_statements):]):
            with st.expander(f"Statement {i+1}: {item['original'][:50]}..."):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Original:**")
                    st.info(item['original'])
                with col2:
                    st.markdown("**Enriched:**")
                    st.success(item['enriched'])
                
                # Display metrics
                st.markdown("**Metrics:**")
                metrics_cols = st.columns(3)
                with metrics_cols[0]:
                    st.metric("TF-IDF Similarity", f"{item['metrics']['cosine_tfidf']:.2f}")
                with metrics_cols[1]:
                    st.metric("Embedding Similarity", f"{item['metrics']['cosine_embedding']:.2f}")
                with metrics_cols[2]:
                    st.metric("Reading Ease", f"{item['metrics']['readability']['estimated_reading_ease']:.1f}") 