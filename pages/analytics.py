import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from services.db.crud._quiz import get_quiz_results_all_users
from components.meta_questions import get_default_criteria

def display_analytics():
    st.title("📊 Analytics Dashboard")
    
    # Get aggregated quiz results for all users
    all_quiz_results = get_quiz_results_all_users()
    
    if not all_quiz_results:
        st.warning("No quiz results available for analysis.")
        st.info("Users need to complete quizzes to generate analytics.")
        st.stop()
    
    # Aggregate the results
    total_original = sum(result["original"] for result in all_quiz_results)
    total_enriched = sum(result["enriched"] for result in all_quiz_results)
    total_responses = total_original + total_enriched
    
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

    # Display overall results
    st.subheader("Overall Statement Preferences")
    
    if total_responses > 0:
        original_percentage = (total_original / total_responses) * 100
        enriched_percentage = (total_enriched / total_responses) * 100
        
        # Create donut chart
        fig = go.Figure(data=[go.Pie(
            labels=["Original Statements", "Personalized Statements"],
            values=[total_original, total_enriched],
            hole=.4,
            marker=dict(colors=['#3498db', '#ff7675']),
            textinfo='label+percent',
            textposition='outside',
            pull=[0.1 if original_percentage > enriched_percentage else 0, 
                  0 if original_percentage > enriched_percentage else 0.1],
            hoverinfo='label+value+percent'
        )])
        
        fig.update_layout(
            title={
                'text': "Statement Preference Distribution",
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
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed Analysis
        st.subheader("Detailed Analysis by Criteria")
        
        # Create tabs for detailed analysis
        tab_titles = ["Understanding", "Readability", "Detail", "Professional Fit", "Self-Assessment"]
        detailed_tabs = st.tabs(tab_titles)
        
        criteria_names = {
            "understand": "Which statement is easier to understand?",
            "read": "Which statement is easier to read?",
            "detail": "Which statement offers greater detail?",
            "profession": "Which statement fits profession better?",
            "assessment": "Which statement is more helpful for self-assessment?"
        }
        
        for tab, key in zip(detailed_tabs, criteria_keys):
            with tab:
                categories = [
                    "Completely prefer orig.",
                    "Somewhat prefer orig.",
                    "Neither",
                    "Somewhat prefer pers.",
                    "Completely prefer pers."
                ]
                
                values = [
                    aggregated_detailed_results[key]["completely_prefer_original"],
                    aggregated_detailed_results[key]["somewhat_prefer_original"],
                    aggregated_detailed_results[key]["neither"],
                    aggregated_detailed_results[key]["somewhat_prefer_enriched"],
                    aggregated_detailed_results[key]["completely_prefer_enriched"]
                ]
                
                # Calculate tendency
                total_responses = sum(values)
                if total_responses > 0:
                    weighted_sum = (values[0] * -2 + values[1] * -1 + values[2] * 0 +
                                 values[3] * 1 + values[4] * 2)
                    tendency = weighted_sum / total_responses
                    tendency_position = (tendency + 2) / 4 * 4
                else:
                    tendency_position = 2
                
                # Create bar chart
                fig = go.Figure()
                
                fig.add_trace(go.Bar(
                    x=categories,
                    y=values,
                    text=values,
                    textposition='auto',
                    marker_color=['#3498db', '#74b9ff', '#e0e0e0', '#ffb8b8', '#ff7675'],
                    hoverinfo='y+text'
                ))
                
                # Add tendency line
                if total_responses > 0:
                    fig.add_shape(
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
                    
                    # Add tendency annotation
                    if tendency < -1:
                        tendency_text = "Strong preference for original statements"
                    elif tendency < 0:
                        tendency_text = "Slight preference for original statements"
                    elif tendency == 0:
                        tendency_text = "No preference"
                    elif tendency < 1:
                        tendency_text = "Slight preference for personalized statements"
                    else:
                        tendency_text = "Strong preference for personalized statements"
                        
                    fig.add_annotation(
                        x=tendency_position,
                        y=max(values) * 1.05 if max(values) > 0 else 5,
                        text=tendency_text,
                        showarrow=True,
                        arrowhead=1,
                        ax=0,
                        ay=-40
                    )
                
                fig.update_layout(
                    title=criteria_names.get(key, key.capitalize()),
                    xaxis=dict(
                        title="Preference",
                        tickangle=-45
                    ),
                    yaxis=dict(
                        title="Number of Responses"
                    ),
                    height=400,
                    margin=dict(t=80, b=120, l=40, r=40)
                )
                
                st.plotly_chart(fig, use_container_width=True)
        
        # Overall interpretation
        st.subheader("Overall Interpretation")
        
        overall_tendency = 0
        total_weights = 0
        
        for key in criteria_keys:
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
        
        if total_weights > 0:
            overall_tendency = overall_tendency / total_weights
            
            if overall_tendency < -1:
                st.info("Overall, users have a strong preference for original statements. They prefer clearer, more concise language.")
            elif overall_tendency < -0.5:
                st.info("Overall, users have a moderate preference for original statements. They seem to value clarity and directness.")
            elif overall_tendency < 0:
                st.info("Overall, users have a slight preference for original statements, but also appreciate some personalization.")
            elif overall_tendency == 0:
                st.info("Overall, users have no strong preference between original and personalized statements.")
            elif overall_tendency < 0.5:
                st.info("Overall, users have a slight preference for personalized statements, but also value clarity.")
            elif overall_tendency < 1:
                st.info("Overall, users have a moderate preference for personalized statements. They appreciate context and detail.")
            else:
                st.info("Overall, users have a strong preference for personalized statements. They value detailed, contextual information.") 