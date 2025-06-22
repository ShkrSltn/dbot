import streamlit as st
import pandas as pd
from services.db.crud._quiz import get_quiz_results_list
from services.db.crud._settings import get_competency_questions_enabled
from services.results_visualization_service import (
    create_preference_pie_chart,
    create_detailed_criterion_chart,
    aggregate_detailed_results,
    create_competency_category_progress_bars,
    create_competency_subcategory_pie_chart,
    process_competency_data,
    create_competency_level_distribution_chart,
    get_tendency_text,
    get_overall_interpretation_text,
    get_criteria_names
)
from components.meta_questions import get_default_criteria

def display_results_step():
    st.subheader("Step 3: Your Results")
    
    # Add Back button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Back", help="Go back to Self-Assessment step"):
            # Import the navigation function
            from pages.user_page.user_flow import navigate_back_to_step
            navigate_back_to_step(2)
    
    # Add dropdown for selecting previous results if they exist
    selected_result = None
    
    # Check if has_previous_results exists in session state
    has_previous_results = st.session_state.get('has_previous_results', False)
    
    # Always check for previous results in case they weren't loaded properly
    if not has_previous_results or 'previous_quiz_results' not in st.session_state:
        db_quiz_results_list = get_quiz_results_list(st.session_state.user["id"])
        st.session_state.has_previous_results = bool(db_quiz_results_list and len(db_quiz_results_list) > 0)
        if st.session_state.has_previous_results:
            st.session_state.previous_quiz_results = db_quiz_results_list
        else:
            # Initialize as an empty list, not None
            st.session_state.previous_quiz_results = []
        has_previous_results = st.session_state.has_previous_results
    
    # To ensure previous_quiz_results is always a list, even if empty
    if 'previous_quiz_results' not in st.session_state or st.session_state.previous_quiz_results is None:
        st.session_state.previous_quiz_results = []
    
    if has_previous_results and 'previous_quiz_results' in st.session_state and st.session_state.previous_quiz_results:
        st.markdown("### View Previous Results")
        
        # Create a more descriptive list of attempts with timestamps if available
        result_options = []
        for i, result in enumerate(st.session_state.previous_quiz_results):
            timestamp = result.get("created_at", "")
            updated_timestamp = result.get("updated_at", "")
            
            if timestamp:
                # Format timestamp if it exists
                if isinstance(timestamp, str):
                    attempt_label = f"Attempt {i+1} ({timestamp})"
                else:
                    # If there is an update time and it is different from the creation time, show it
                    if updated_timestamp and updated_timestamp != timestamp:
                        if isinstance(updated_timestamp, str):
                            attempt_label = f"Attempt {i+1} ({timestamp.strftime('%Y-%m-%d %H:%M')}, upd: {updated_timestamp})"
                        else:
                            attempt_label = f"Attempt {i+1} ({timestamp.strftime('%Y-%m-%d %H:%M')}, upd: {updated_timestamp.strftime('%Y-%m-%d %H:%M')})"
                    else:
                        attempt_label = f"Attempt {i+1} ({timestamp.strftime('%Y-%m-%d %H:%M')})"
            else:
                attempt_label = f"Attempt {i+1}"
            result_options.append(attempt_label)
        
        if 'quiz_results' in st.session_state and (st.session_state.quiz_results.get("original", 0) > 0 or 
                                                  st.session_state.quiz_results.get("enriched", 0) > 0):
            result_options.append("Current Attempt")
        
        if result_options:
            # Use a unique key for the selectbox to ensure it updates properly
            selected_attempt = st.selectbox(
                "Select attempt to view:", 
                result_options,
                key="result_selector"
            )
            
            if selected_attempt != "Current Attempt":
                attempt_index = int(selected_attempt.split()[1]) - 1
                selected_result = st.session_state.previous_quiz_results[attempt_index]
        
        # Add a button to start a new assessment
        if st.button("Start New Assessment"):
            # Reset all quiz-related session state
            reset_quiz_session_state()
            st.session_state.flow_step = 1
            st.rerun()
    
    # Use either selected previous result or current results
    if selected_result:
        display_results = selected_result
        
        # Add display of creation and update dates if they exist
        created_at = display_results.get("created_at")
        updated_at = display_results.get("updated_at")
        
        if created_at and not isinstance(created_at, str):
            st.caption(f"Created: {created_at.strftime('%Y-%m-%d %H:%M')}")
            
            # Show update date only if it is different from the creation date
            if updated_at and updated_at != created_at and not isinstance(updated_at, str):
                st.caption(f"Last updated: {updated_at.strftime('%Y-%m-%d %H:%M')}")
    elif 'quiz_results' in st.session_state:
        display_results = {
            "original": st.session_state.quiz_results.get("original", 0),
            "enriched": st.session_state.quiz_results.get("enriched", 0),
            "neither": st.session_state.quiz_results.get("neither", 0),
            "detailed_results": st.session_state.get("detailed_quiz_results", {}),
            "competency_results": st.session_state.get("competency_results", [])
        }
    else:
        display_results = {"original": 0, "enriched": 0, "neither": 0, "detailed_results": {}, "competency_results": []}

    # Check if there are any responses (including "neither")
    total_responses = display_results.get("original", 0) + display_results.get("enriched", 0) + display_results.get("neither", 0)
    
    if total_responses == 0:
        st.warning("No self-assessment results available for this attempt. Please complete the self-assessment first.")
        
        # If user has no results at all, offer to start the assessment
        if not has_previous_results:
            if st.button("Start Assessment"):
                reset_quiz_session_state()
                st.session_state.flow_step = 1
                st.rerun()
    else:
        # Check the competency questions display setting
        show_competency_tab = get_competency_questions_enabled()

        # Create tabs depending on the competency questions display setting
        if show_competency_tab:
            tab_preferences, tab_competency = st.tabs(["Statement Preferences", "Competency Assessment"])
            
            with tab_preferences:
                # Display preference results in the first tab
                display_results_summary(display_results, total_responses)
                display_detailed_results(display_results)
            
            with tab_competency:
                # Display competency results in the second tab
                display_competency_results(display_results)
        else:
            # Show only one tab with preferences
            st.markdown("### Statement Preferences")
            display_results_summary(display_results, total_responses)
            display_detailed_results(display_results)
        
        display_restart_option()

def reset_quiz_session_state():
    """Reset all self-assessment-related session state variables"""
    # Reset self-assessment results
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
    
    # Reset competency results
    st.session_state.competency_results = []
    
    # Reset shown indices
    st.session_state.quiz_shown_indices = []

def display_results_summary(display_results, total_responses):
    st.success("Congratulations! You've completed the assessment.")
    
    # Display results summary
    st.markdown("### Your Statement Preferences")
    
    # Get values with defaults to handle older results without "neither"
    original_count = display_results.get("original", 0)
    enriched_count = display_results.get("enriched", 0)
    neither_count = display_results.get("neither", 0)
    
    # Create pie chart using the visualization service
    fig = create_preference_pie_chart(original_count, enriched_count, neither_count, 
                                    chart_key="summary_pie_chart")
    
    if fig:
        st.plotly_chart(fig, use_container_width=True, key="summary_pie_chart")

def display_detailed_results(display_results):
    # Display detailed results by criteria
    st.markdown("### Detailed Results by Criteria")
    
    # Get criteria and names
    default_criteria = get_default_criteria()
    criteria_keys = list(default_criteria.keys())
    criteria_names = get_criteria_names()
    
    # Get detailed results safely
    detailed_results = display_results.get("detailed_results", {})
    
    # Calculate overall tendency
    overall_tendency = 0
    total_weights = 0
    
    # Display criteria in pairs (2 columns)
    for i in range(0, len(criteria_keys), 2):
        # Create two columns
        cols = st.columns(2)
        
        # Process up to 2 criteria in this row
        for col_idx in range(2):
            criteria_idx = i + col_idx
            
            # Check if we still have criteria to display
            if criteria_idx < len(criteria_keys):
                key = criteria_keys[criteria_idx]
                name = criteria_names.get(key, key.capitalize())
                
                # Display in the appropriate column
                with cols[col_idx]:
                    st.subheader(f"{criteria_idx+1}. {name}")
                    
                    # Safely get values for each criterion
                    criterion_data = detailed_results.get(key, {})
                    values = [
                        criterion_data.get("completely_prefer_original", 0),
                        criterion_data.get("somewhat_prefer_original", 0),
                        criterion_data.get("neither", 0),
                        criterion_data.get("somewhat_prefer_enriched", 0),
                        criterion_data.get("completely_prefer_enriched", 0)
                    ]
                    
                    total = sum(values)
                    if total > 0:
                        # Create chart using visualization service
                        detail_fig, tendency = create_detailed_criterion_chart(values, name, f"detail_chart_{key}")
                        
                        if detail_fig:
                            overall_tendency += tendency * total
                            total_weights += total
                            st.plotly_chart(detail_fig, use_container_width=True, key=f"detail_chart_{key}")
                    else:
                        st.info(f"No data available for {name} yet.")
        
        # Add a divider after each row (except the last one)
        if i + 2 < len(criteria_keys):
            st.divider()
    
    # Calculate overall tendency if we have data
    if total_weights > 0:
        overall_tendency = overall_tendency / total_weights
        
        # Display overall interpretation
        st.subheader("Overall Interpretation")
        interpretation_text = get_overall_interpretation_text(overall_tendency, is_global=False)
        st.info(interpretation_text)

def display_competency_results(display_results):
    """Display the competency assessment results using pie charts"""
    
    competency_results = display_results.get("competency_results", [])
    
    if not competency_results:
        st.info("No competency assessment data available for this attempt.")
        return
    
    st.markdown("### Your Digital Competency Self-Assessment")
    
    # Process competency data using visualization service
    df = process_competency_data(competency_results)
    
    if df is None:
        st.info("No competency assessment data available.")
        return
    
    # For categories
    category_scores = df.groupby("Category")["Competency_Value"].agg(["mean", "count"]).reset_index()
    category_scores["score_percentage"] = (category_scores["mean"] / 5) * 100
    
    # Create the digital competence visualization with horizontal bars for categories
    st.subheader("Digital Competence")
    create_competency_category_progress_bars(category_scores)
    
    # Create pie chart using visualization service
    fig = create_competency_subcategory_pie_chart(df, chart_key="subcategory_pie")
    st.plotly_chart(fig, use_container_width=True, key="subcategory_pie")
    
    # Create expandable sections for detailed subcategory info
    st.subheader("Detailed Competency Analysis")
    
    for category in df["Category"].unique():
        with st.expander(f"{category}", expanded=False):
            category_df = df[df["Category"] == category]
            
            # Show detailed statements for each subcategory
            subcategories = category_df["Subcategory"].unique()
            
            for subcategory in subcategories:
                st.markdown(f"#### {subcategory}")
                
                subcategory_df = category_df[category_df["Subcategory"] == subcategory]
                
                # Calculate percentage
                subcategory_percentage = (subcategory_df["Competency_Value"].mean() / 5) * 100
                
                # Create a progress bar
                st.progress(subcategory_percentage / 100, f"{subcategory_percentage:.0f}%")
                
                # Show statement details
                for _, row in subcategory_df.iterrows():
                    statement = row["Statement"]
                    competency = row["Competency_Level"]
                    
                    # Color code based on competency
                    colors = {
                        "No knowledge": "#a3652f",
                        "Basic": "#2f2fa3",
                        "Intermediate": "#a32f2f",
                        "Advanced": "#2fa32f"
                    }
                    
                    bg_color = colors.get(competency, "#ffffff")
                    
                    # Create a styled container for the statement
                    st.markdown(f"""
                    <div style="background-color: {bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 5px;">
                        <div style="display: flex; justify-content: space-between;">
                            <div style="flex: 4;">{statement}</div>
                            <div style="flex: 1; text-align: right; font-weight: bold;">{competency}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

def display_restart_option():
    # Option to restart the quiz
    if st.button("Restart Assessment"):
        # Reset quiz results in both session and database
        reset_quiz_session_state()
        st.session_state.flow_step = 1
        st.rerun()
