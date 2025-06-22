import streamlit as st
import pandas as pd
from services.db.crud._quiz import get_quiz_results_all_users
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

def display_analytics():
    # Проверка прав админа
    if st.session_state.get('current_role') != 'admin':
        st.error("🚫 Access denied. This page is only available to administrators.")
        st.info("Please contact an administrator if you need access to analytics.")
        return
    
    st.title("📊 Analytics Dashboard")
    st.markdown("### Global Results from All Users")
    
    # Get aggregated quiz results for all users
    all_quiz_results = get_quiz_results_all_users()
    
    if not all_quiz_results:
        st.warning("No quiz results available for analysis.")
        st.info("Users need to complete assessments to generate analytics.")
        st.stop()
    
    # Check the competency questions display setting
    show_competency_tab = get_competency_questions_enabled()
    
    # Calculate total responses
    total_responses = sum(
        result.get("original", 0) + result.get("enriched", 0) + result.get("neither", 0) 
        for result in all_quiz_results
    )
    
    if total_responses == 0:
        st.warning("No assessment responses available for analysis.")
        st.stop()
    
    # Create tabs depending on the competency questions display setting
    if show_competency_tab:
        tab_preferences, tab_competency = st.tabs(["Statement Preferences", "Competency Assessment"])
        
        with tab_preferences:
            # Display preference results in the first tab
            display_global_preferences_summary(all_quiz_results, total_responses)
            display_global_detailed_results(all_quiz_results)
        
        with tab_competency:
            # Display competency results in the second tab
            display_global_competency_results(all_quiz_results)
    else:
        # Show only statement preferences
        st.markdown("### Statement Preferences Analysis")
        display_global_preferences_summary(all_quiz_results, total_responses)
        display_global_detailed_results(all_quiz_results)

def display_global_preferences_summary(all_quiz_results, total_responses):
    """Display summary of global statement preferences"""
    
    # Aggregate the results
    total_original = sum(result.get("original", 0) for result in all_quiz_results)
    total_enriched = sum(result.get("enriched", 0) for result in all_quiz_results)
    total_neither = sum(result.get("neither", 0) for result in all_quiz_results)
    
    # Display summary statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", len(all_quiz_results))
    with col2:
        st.metric("Total Responses", total_responses)
    with col3:
        st.metric("Prefer Original", f"{total_original} ({(total_original/total_responses*100):.1f}%)")
    with col4:
        st.metric("Prefer Personalized", f"{total_enriched} ({(total_enriched/total_responses*100):.1f}%)")
    
    st.markdown("### Overall Statement Preference Distribution")
    
    if total_responses > 0:
        # Create pie chart using visualization service
        title_suffix = f" (n={len(all_quiz_results)} users)"
        fig = create_preference_pie_chart(total_original, total_enriched, total_neither,
                                        title_suffix=title_suffix, chart_key="global_summary_pie_chart")
        
        if fig:
            # Add total responses annotation in center
            fig.add_annotation(
                text=f'Total Responses: {total_responses}',
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )
            st.plotly_chart(fig, use_container_width=True, key="global_summary_pie_chart")

def display_global_detailed_results(all_quiz_results):
    """Display detailed results by criteria for all users"""
    
    st.markdown("### Detailed Analysis by Criteria")
    
    # Aggregate detailed results using visualization service
    aggregated_detailed_results = aggregate_detailed_results(all_quiz_results)
    criteria_names = get_criteria_names()
    criteria_keys = list(aggregated_detailed_results.keys())
    
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
                    values = [
                        aggregated_detailed_results[key]["completely_prefer_original"],
                        aggregated_detailed_results[key]["somewhat_prefer_original"],
                        aggregated_detailed_results[key]["neither"],
                        aggregated_detailed_results[key]["somewhat_prefer_enriched"],
                        aggregated_detailed_results[key]["completely_prefer_enriched"]
                    ]
                    
                    total = sum(values)
                    if total > 0:
                        # Create chart using visualization service
                        detail_fig, tendency = create_detailed_criterion_chart(values, name, f"global_detail_chart_{key}")
                        
                        if detail_fig:
                            overall_tendency += tendency * total
                            total_weights += total
                            st.plotly_chart(detail_fig, use_container_width=True, key=f"global_detail_chart_{key}")
                    else:
                        st.info(f"No data available for {name} yet.")
        
        # Add a divider after each row (except the last one)
        if i + 2 < len(criteria_keys):
            st.divider()
    
    # Calculate overall tendency if we have data
    if total_weights > 0:
        overall_tendency = overall_tendency / total_weights
        
        # Display overall interpretation
        st.subheader("Overall Global Interpretation")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            interpretation_text = get_overall_interpretation_text(overall_tendency, is_global=True)
            st.info(interpretation_text)
        
        with col2:
            # Display tendency as a gauge
            tendency_percentage = ((overall_tendency + 2) / 4) * 100
            st.metric("Global Tendency", f"{tendency_percentage:.1f}%", 
                     help="0% = Strong preference for original, 100% = Strong preference for personalized")

def display_global_competency_results(all_quiz_results):
    """Display aggregated competency assessment results from all users"""
    
    st.markdown("### Global Digital Competency Analysis")
    
    # Collect all competency results from all users
    all_competency_data = []
    
    for result in all_quiz_results:
        competency_results = result.get("competency_results", [])
        if competency_results:
            for comp in competency_results:
                all_competency_data.append({
                    "Category": comp.get("category", "Unknown"),
                    "Subcategory": comp.get("subcategory", "Unknown"),
                    "Statement": comp.get("statement", ""),
                    "Competency": comp.get("competency", "Intermediate")
                })
    
    if not all_competency_data:
        st.info("No competency assessment data available from users.")
        return
    
    # Process competency data using visualization service
    df = process_competency_data(all_competency_data)
    
    if df is None:
        st.info("No competency assessment data available.")
        return
    
    # Display summary statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Assessments", len(df))
    with col2:
        avg_competency = df["Competency_Value"].mean()
        st.metric("Average Competency", f"{avg_competency:.1f}/5.0")
    with col3:
        competency_percentage = (avg_competency / 5) * 100
        st.metric("Global Competency %", f"{competency_percentage:.1f}%")
    
    # For categories
    category_scores = df.groupby("Category")["Competency_Value"].agg(["mean", "count"]).reset_index()
    category_scores["score_percentage"] = (category_scores["mean"] / 5) * 100
    
    # Create the digital competence visualization with horizontal bars for categories
    st.subheader("Global Digital Competence by Category")
    create_competency_category_progress_bars(category_scores)
    
    # Create pie chart using visualization service
    fig = create_competency_subcategory_pie_chart(df, title="Global Competency by Subcategory", 
                                                chart_key="global_subcategory_pie")
    st.plotly_chart(fig, use_container_width=True, key="global_subcategory_pie")
    
    # Detailed breakdown by competency level
    st.subheader("Competency Level Distribution")
    
    # Create distribution chart using visualization service
    level_fig = create_competency_level_distribution_chart(df, 
                                                         title="Distribution of Competency Levels Across All Users",
                                                         chart_key="global_competency_distribution")
    st.plotly_chart(level_fig, use_container_width=True, key="global_competency_distribution")
    
    # Create expandable sections for detailed analysis
    st.subheader("Detailed Global Analysis by Category")
    
    for category in df["Category"].unique():
        with st.expander(f"📊 {category}", expanded=False):
            category_df = df[df["Category"] == category]
            
            # Show stats for this category
            cat_avg = category_df["Competency_Value"].mean()
            cat_count = len(category_df)
            cat_percentage = (cat_avg / 5) * 100
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Responses", cat_count)
            with col2:
                st.metric("Average Score", f"{cat_avg:.1f}/5.0")
            with col3:
                st.metric("Percentage", f"{cat_percentage:.1f}%")
            
            # Show subcategory breakdown
            subcategories = category_df["Subcategory"].unique()
            
            for subcategory in subcategories:
                st.markdown(f"#### {subcategory}")
                
                subcategory_df = category_df[category_df["Subcategory"] == subcategory]
                subcat_avg = subcategory_df["Competency_Value"].mean()
                subcat_percentage = (subcat_avg / 5) * 100
                subcat_count = len(subcategory_df)
                
                # Create a progress bar
                st.progress(subcat_percentage / 100, f"{subcat_percentage:.0f}% (n={subcat_count})")
                
                # Show competency level distribution for this subcategory
                subcat_levels = subcategory_df["Competency_Level"].value_counts()
                if len(subcat_levels) > 0:
                    level_text = " | ".join([f"{level}: {count}" for level, count in subcat_levels.items()])
                    st.caption(f"Distribution: {level_text}") 