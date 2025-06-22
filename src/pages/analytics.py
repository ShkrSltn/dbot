import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from services.db.crud._quiz import get_quiz_results_all_users
from services.db.crud._settings import get_competency_questions_enabled
from components.meta_questions import get_default_criteria

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
        original_percentage = (total_original / total_responses) * 100
        enriched_percentage = (total_enriched / total_responses) * 100
        neither_percentage = (total_neither / total_responses) * 100
        
        # Create donut chart
        labels = ["Original Statements", "Personalized Statements", "No Preference"]
        values = [total_original, total_enriched, total_neither]
        colors = ['#3498db', '#ff7675', '#95a5a6']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=.4,
            marker=dict(colors=colors),
            textinfo='label+percent',
            textposition='outside',
            pull=[0.1 if original_percentage > max(enriched_percentage, neither_percentage) else 0, 
                  0.1 if enriched_percentage > max(original_percentage, neither_percentage) else 0,
                  0.1 if neither_percentage > max(original_percentage, enriched_percentage) else 0],
            hoverinfo='label+value+percent',
            insidetextorientation='radial'
        )])
        
        fig.update_layout(
            title={
                'text': f"Global Preference Distribution (n={len(all_quiz_results)} users)",
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5
            ),
            height=500,
            margin=dict(t=80, b=80, l=40, r=40),
            annotations=[dict(
                text=f'Total Responses: {total_responses}',
                x=0.5, y=0.5,
                font_size=20,
                showarrow=False
            )]
        )
        
        st.plotly_chart(fig, use_container_width=True, key="global_summary_pie_chart")

def display_global_detailed_results(all_quiz_results):
    """Display detailed results by criteria for all users"""
    
    st.markdown("### Detailed Analysis by Criteria")
    
    # Get default criteria to use the right keys
    default_criteria = get_default_criteria()
    criteria_keys = list(default_criteria.keys())
    
    # Aggregate detailed results
    aggregated_detailed_results = {
        key: {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, 
              "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0} 
        for key in criteria_keys
    }
    
    for result in all_quiz_results:
        detailed = result.get("detailed_results", {})
        for criterion in criteria_keys:
            if criterion in detailed:
                criterion_data = detailed[criterion]
                for preference in aggregated_detailed_results[criterion]:
                    if preference in criterion_data:
                        aggregated_detailed_results[criterion][preference] += criterion_data[preference]
    
    # Define criteria names
    criteria_names = {
        "understand": "Understanding",
        "read": "Readability", 
        "detail": "Detail",
        "profession": "Professional Relevance",
        "assessment": "Self-Assessment"
    }
    
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
                        weighted_sum = (values[0] * -2 + values[1] * -1 + values[2] * 0 + 
                                      values[3] * 1 + values[4] * 2)
                        tendency = weighted_sum / total
                        overall_tendency += tendency * total
                        total_weights += total
                        
                        # Create the bar chart
                        categories = [
                            "Completely prefer orig.", 
                            "Somewhat prefer orig.", 
                            "Neither", 
                            "Somewhat prefer pers.", 
                            "Completely prefer pers."
                        ]
                        
                        # Calculate the tendency line position
                        tendency_position = (tendency + 2) / 4 * 4  # Map from -2 to 2 range to 0 to 4 range
                        
                        # Create the bar chart
                        detail_fig = go.Figure()
                        
                        # Add bars with consistent colors for all criteria
                        detail_fig.add_trace(go.Bar(
                            x=categories,
                            y=values,
                            text=values,
                            textposition='auto',
                            marker_color=['#3498db', '#74b9ff', '#e0e0e0', '#ffb8b8', '#ff7675'],
                            hoverinfo='y+text'
                        ))
                        
                        # Add tendency line
                        detail_fig.add_shape(
                            type="line",
                            x0=tendency_position,
                            y0=0,
                            x1=tendency_position,
                            y1=max(values) * 1.1 if max(values) > 0 else 10,
                            line=dict(
                                color="red",
                                width=2,
                                dash="dash",
                            )
                        )
                        
                        # Add annotation for the tendency
                        if tendency < -1:
                            tendency_text = "Strong preference for original"
                        elif tendency < -0.1:
                            tendency_text = "Slight preference for original"
                        elif tendency <= 0.1:
                            tendency_text = "No preference"
                        elif tendency < 1:
                            tendency_text = "Slight preference for personalized"
                        else:
                            tendency_text = "Strong preference for personalized"
                            
                        detail_fig.add_annotation(
                            x=tendency_position,
                            y=max(values) * 1.05 if max(values) > 0 else 5,
                            text=tendency_text,
                            showarrow=True,
                            arrowhead=1,
                            ax=0,
                            ay=-40
                        )
                        
                        # Update layout - adjust for smaller width
                        detail_fig.update_layout(
                            xaxis=dict(
                                title="Preference",
                                tickangle=-45,
                                tickfont=dict(size=9)
                            ),
                            yaxis=dict(
                                title="Number of Responses"
                            ),
                            height=350,
                            margin=dict(t=30, b=100, l=30, r=30),
                            font=dict(size=10)
                        )
                        
                        # Add unique key for each plotly chart
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
            if overall_tendency < -1:
                st.info("🔵 Overall, users strongly prefer original statements. They value clarity and directness.")
            elif overall_tendency < -0.1:
                st.info("🔵 Overall, users somewhat prefer original statements. They lean towards clearer, more concise language.")
            elif overall_tendency <= 0.1:
                st.info("⚪ Overall, users have no strong preference between original and personalized statements.")
            elif overall_tendency < 1:
                st.info("🔴 Overall, users somewhat prefer personalized statements. They appreciate context and detail.")
            else:
                st.info("🔴 Overall, users strongly prefer personalized statements. They value detailed, contextual information.")
        
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
    
    # Create a DataFrame
    df = pd.DataFrame(all_competency_data)
    
    # Map from responses to levels
    response_to_level = {
        "I have no knowledge of this / I never heard of this": "No knowledge",
        "I have only a limited understanding of this and need more explanations": "Basic",
        "I have a good understanding of this": "Intermediate",
        "I fully master this topic/issue and I could explain it to others": "Advanced",
        # Add short formats for backward compatibility
        "No knowledge": "No knowledge",
        "Basic": "Basic",
        "Intermediate": "Intermediate",
        "Advanced": "Advanced"
    }
    
    # Add numeric mapping for competency for visualization
    competency_map = {
        "No knowledge": 1,
        "Basic": 2,
        "Intermediate": 3,
        "Advanced": 4,
        "Expert": 5
    }
    
    # Convert response text to levels
    df["Competency_Level"] = df["Competency"].map(response_to_level)
    df["Competency_Value"] = df["Competency_Level"].map(competency_map)
    
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
    
    # Overall competency percentage
    overall_score_percentage = (df["Competency_Value"].mean() / 5) * 100
    
    # Create the digital competence visualization with horizontal bars for categories
    st.subheader("Global Digital Competence by Category")
    
    # Create horizontal progress bars for each category
    for i, row in category_scores.iterrows():
        category = row["Category"]
        percentage = row["score_percentage"]
        count = row["count"]
        
        # Define colors based on category
        colors = {
            "Information and data literacy": "#3498db",  # Blue
            "Communication and collaboration": "#e74c3c",  # Red
            "Digital content creation": "#f1c40f",  # Yellow
            "Safety": "#2ecc71",  # Green
            "Problem solving": "#e67e22"   # Orange
        }
        
        color = colors.get(category, "#3498db")
        
        # Create container with background color
        container_html = f"""
        <div style="background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 3;">{category} (n={count})</div>
                <div style="flex: 7; background-color: #f0f0f0; height: 30px; border-radius: 15px; position: relative;">
                    <div style="position: absolute; width: {percentage}%; height: 100%; background-color: {color}; border-radius: 15px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-weight: bold;">{percentage:.0f}%</span>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(container_html, unsafe_allow_html=True)
    
    # Create main pie chart with subcategories
    subcategory_data = df.groupby(["Category", "Subcategory"])["Competency_Value"].agg(["mean", "count"]).reset_index()
    subcategory_data["Percentage"] = (subcategory_data["mean"] / 5) * 100
    
    # Define colors for each category
    color_map = {
        "Information and data literacy": "#3498db",
        "Communication and collaboration": "#e74c3c",
        "Digital content creation": "#f1c40f",
        "Safety": "#2ecc71",
        "Problem solving": "#e67e22"
    }
    
    # Create a list of colors based on the category of each subcategory
    subcategory_colors = []
    for category in subcategory_data["Category"]:
        base_color = color_map.get(category, "#3498db")
        subcategory_colors.append(base_color)
    
    # Create the pie chart
    fig = go.Figure(data=[go.Pie(
        labels=subcategory_data["Subcategory"],
        values=subcategory_data["Percentage"],
        hole=0.3,
        marker=dict(
            colors=subcategory_colors,
            line=dict(color='#FFFFFF', width=2)
        ),
        textinfo='label+percent',
        textposition='outside',
        insidetextorientation='radial',
        textfont=dict(size=10),
        hoverinfo='label+value+percent',
        hovertemplate='<b>%{label}</b><br>Average Score: %{value:.1f}%<br>Count: %{customdata}<extra></extra>',
        customdata=subcategory_data["count"]
    )])
    
    # Add text in the center
    fig.add_annotation(
        x=0.5, y=0.5,
        text=f"{overall_score_percentage:.0f}%",
        font=dict(size=24, color='#333333'),
        showarrow=False
    )
    
    # Update layout
    fig.update_layout(
        title={
            'text': "Global Competency by Subcategory",
            'y':0.95,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        height=600,
        showlegend=False,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    # Display the pie chart
    st.plotly_chart(fig, use_container_width=True, key="global_subcategory_pie")
    
    # Detailed breakdown by competency level
    st.subheader("Competency Level Distribution")
    
    # Count responses by competency level
    level_counts = df["Competency_Level"].value_counts()
    
    # Create bar chart for competency levels
    level_fig = go.Figure()
    
    level_colors = {
        "No knowledge": "#e74c3c",
        "Basic": "#f39c12", 
        "Intermediate": "#f1c40f",
        "Advanced": "#2ecc71"
    }
    
    levels = ["No knowledge", "Basic", "Intermediate", "Advanced"]
    counts = [level_counts.get(level, 0) for level in levels]
    colors = [level_colors.get(level, "#95a5a6") for level in levels]
    
    level_fig.add_trace(go.Bar(
        x=levels,
        y=counts,
        text=counts,
        textposition='auto',
        marker_color=colors,
        hoverinfo='y+text'
    ))
    
    level_fig.update_layout(
        title="Distribution of Competency Levels Across All Users",
        xaxis=dict(title="Competency Level"),
        yaxis=dict(title="Number of Responses"),
        height=400,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
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