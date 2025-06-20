import streamlit as st
import pandas as pd
from services.enrichment_service import enrich_statement_with_llm
from services.metrics_service import calculate_quality_metrics
from services.statement_service import get_category_for_statement
from services.db.crud._statements import save_statement

def display_enrichment_demo(sample_statements):
    st.title("✨ Enrichment Demo")
    
    # Debug information
    st.write("DEBUG: Entering Enrichment Demo page")
    print("DEBUG: Entering Enrichment Demo page")

    if not st.session_state.profile["job_role"]:
        st.warning("Please create your profile first in the Profile Builder section.")
        print("DEBUG: Profile not created, stopping execution")
        st.stop()

    st.markdown("""
    This demo shows how DigiBot enriches statements based on your profile.
    Select a statement from the dropdown or enter your own, then click "Enrich Statement" to see the result.
    """)

    col1, col2 = st.columns([3, 1])

    with col1:
        statement_option = st.selectbox(
            "Select a statement or choose 'Custom' to enter your own:",
            ["Custom"] + sample_statements
        )
        print(f"DEBUG: Selected statement option: {statement_option}")

        if statement_option == "Custom":
            original_statement = st.text_area("Enter your statement:", height=100)
        else:
            original_statement = statement_option
        print(f"DEBUG: Original statement: {original_statement}")

        statement_length = st.slider("Statement Length (characters)", 100, 300, 150)
        print(f"DEBUG: Statement length: {statement_length}")

    with col2:
        st.subheader("Your Profile")
        for key, value in st.session_state.profile.items():
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")

    if st.button("Enrich Statement") and original_statement:
        print("DEBUG: Enrich Statement button clicked")
        try:
            print("DEBUG: Starting enrichment process")
            with st.spinner("Enriching statement..."):
                # Create context from profile
                context = ", ".join(
                    [f"{k.replace('_', ' ').title()}: {v}" for k, v in st.session_state.profile.items() if v])
                print(f"DEBUG: Created context: {context[:100]}...")

                # Get category and subcategory for the statement
                category, subcategory = get_category_for_statement(original_statement)
                print(f"DEBUG: Category: {category}, Subcategory: {subcategory}")

                # Enrich statement
                print("DEBUG: Calling enrich_statement_with_llm")
                enriched_statement = enrich_statement_with_llm(context, original_statement, statement_length)
                print(f"DEBUG: Received enriched statement: {enriched_statement[:100]}...")

                # Calculate quality metrics
                print("DEBUG: Calculating quality metrics")
                metrics = calculate_quality_metrics(original_statement, enriched_statement)
                print(f"DEBUG: Metrics calculated: {metrics}")

                # Save to session state with category and subcategory
                statement_data = {
                    "original": original_statement,
                    "enriched": enriched_statement,
                    "metrics": metrics,
                    "category": category,
                    "subcategory": subcategory
                }
                
                st.session_state.enriched_statements.append(statement_data)
                
                # Сохраняем в базу данных
                statement_id = save_statement(
                    st.session_state.user["id"],
                    original_statement,
                    enriched_statement,
                    metrics
                )
                
                if statement_id:
                    st.success(f"Statement saved to database with ID: {statement_id}")

            # Display results
            print("DEBUG: Displaying results")
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
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("TF-IDF Similarity", f"{metrics['cosine_tfidf']:.2f}")

            with col2:
                st.metric("Embedding Similarity", f"{metrics['cosine_embedding']:.2f}")

            with col3:
                st.metric("Reading Ease", f"{metrics['readability']['estimated_reading_ease']:.1f}")

            # Show detailed readability metrics
            with st.expander("Detailed Readability Metrics"):
                readability_df = pd.DataFrame([metrics['readability']])
                st.dataframe(readability_df)
                
        except Exception as e:
            print(f"DEBUG: Error in enrichment process: {str(e)}")
            st.error(f"Error processing statement: {str(e)}")
            st.info("Please try again with a different statement or check your connection.") 