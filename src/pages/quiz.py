import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from services.db.crud._quiz import save_quiz_results 

def display_quiz():
    st.title("🧠 Statement Preference Quiz")
    
    if len(st.session_state.enriched_statements) < 1:  # Changed from 3 to 1 for easier testing
        st.warning("Please enrich at least one statement before taking the quiz.")
        st.info("Go to the Enrichment Demo or Batch Enrichment page to create more statements.")
        st.stop()
        
    st.markdown("""
    This quiz helps us understand your preferences between original and enriched statements.
    For each pair, evaluate the statements based on different criteria. 
    """)
    
    # Select a random statement that hasn't been shown in the quiz yet
    if 'quiz_shown_indices' not in st.session_state:
        st.session_state.quiz_shown_indices = []
        
    available_indices = [i for i in range(len(st.session_state.enriched_statements)) 
                        if i not in st.session_state.quiz_shown_indices]
    
    if not available_indices:
        st.success("You've completed the quiz for all available statements!")
        
        # Show a summary of results
        st.subheader("Your Preferences Summary")
        
        total_responses = st.session_state.quiz_results["original"] + st.session_state.quiz_results["enriched"]
        if total_responses > 0:
            original_percentage = (st.session_state.quiz_results["original"] / total_responses) * 100
            enriched_percentage = (st.session_state.quiz_results["enriched"] / total_responses) * 100
            
            # Create interactive pie chart with Plotly
            labels = ["Original Statements", "Personalized Statements"]
            values = [st.session_state.quiz_results["original"], st.session_state.quiz_results["enriched"]]
            
            # Define colors
            colors = ['#3498db', '#ff7675']
            
            # Create figure
            fig = go.Figure(data=[go.Pie(
                labels=labels,
                values=values,
                hole=.4,  # Creates a donut chart
                marker=dict(colors=colors),
                textinfo='label+percent',
                textposition='outside',
                pull=[0.1 if original_percentage > enriched_percentage else 0, 
                      0 if original_percentage > enriched_percentage else 0.1],
                hoverinfo='label+value+percent'
            )])
            
            # Update layout
            fig.update_layout(
                title={
                    'text': "Statement Preference Distribution",
                    'y':0.95,
                    'x':0.5,
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
                    text=f'Total: {total_responses}',
                    x=0.5, y=0.5,
                    font_size=20,
                    showarrow=False
                )]
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Save quiz results to database
            save_quiz_results(
                st.session_state.user["id"],
                st.session_state.quiz_results["original"],
                st.session_state.quiz_results["enriched"],
                st.session_state.detailed_quiz_results
            )
            
            # Create detailed analysis charts
            st.subheader("Detailed Analysis by Criteria")
            
            # Create a 2x3 grid for the detailed charts
            detailed_tabs = st.tabs(["Understanding", "Readability", "Detail", "Professional Fit", "Self-Assessment"])
            
            criteria_names = {
                "understand": "Which statement is easier to understand?",
                "read": "Which statement is easier to read?",
                "detail": "Which statement offers greater detail?",
                "profession": "Which statement fits your profession?",
                "assessment": "Which statement is helpful for a self-assessment?"
            }
            
            criteria_keys = ["understand", "read", "detail", "profession", "assessment"]
            
            for i, (tab, key) in enumerate(zip(detailed_tabs, criteria_keys)):
                with tab:
                    # Create data for the bar chart
                    categories = [
                        "Completely prefer orig.", 
                        "Somewhat prefer orig.", 
                        "Neither", 
                        "Somewhat prefer pers.", 
                        "Completely prefer pers."
                    ]
                    
                    values = [
                        st.session_state.detailed_quiz_results[key]["completely_prefer_original"],
                        st.session_state.detailed_quiz_results[key]["somewhat_prefer_original"],
                        st.session_state.detailed_quiz_results[key]["neither"],
                        st.session_state.detailed_quiz_results[key]["somewhat_prefer_enriched"],
                        st.session_state.detailed_quiz_results[key]["completely_prefer_enriched"]
                    ]
                    
                    # Calculate the tendency line position
                    total_responses = sum(values)
                    if total_responses > 0:
                        weighted_sum = (values[0] * -2 + values[1] * -1 + values[2] * 0 + 
                                       values[3] * 1 + values[4] * 2)
                        tendency = weighted_sum / total_responses
                        # Map from -2 to 2 range to 0 to 4 range for x-position
                        tendency_position = (tendency + 2) / 4 * 4
                    else:
                        tendency_position = 2  # Middle position if no data
                    
                    # Create the bar chart
                    fig = go.Figure()
                    
                    # Add bars
                    fig.add_trace(go.Bar(
                        x=categories,
                        y=values,
                        text=values,
                        textposition='auto',
                        marker_color=['#3498db', '#74b9ff', '#e0e0e0', '#ffb8b8', '#ff7675'],
                        hoverinfo='y+text'
                    ))
                    
                    # Add tendency line
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
                    
                    # Update layout
                    fig.update_layout(
                        title=criteria_names[key],
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
                    
                    # Add annotation for the tendency
                    if total_responses > 0:
                        if tendency < -1:
                            tendency_text = "Strong preference for personalized statements"
                        elif tendency < 0:
                            tendency_text = "Slight preference for personalized statements"
                        elif tendency == 0:
                            tendency_text = "No preference"
                        elif tendency < 1:
                            tendency_text = "Slight preference for original statements"
                        else:
                            tendency_text = "Strong preference for original statements"
                            
                        fig.add_annotation(
                            x=tendency_position,
                            y=max(values) * 1.05 if max(values) > 0 else 5,
                            text=tendency_text,
                            showarrow=True,
                            arrowhead=1,
                            ax=0,
                            ay=-40
                        )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            # Add interpretation
            st.subheader("Interpretation")
            
            # Calculate overall tendency
            overall_tendency = 0
            total_weights = 0
            
            for key in criteria_keys:
                values = [
                    st.session_state.detailed_quiz_results[key]["completely_prefer_original"],
                    st.session_state.detailed_quiz_results[key]["somewhat_prefer_original"],
                    st.session_state.detailed_quiz_results[key]["neither"],
                    st.session_state.detailed_quiz_results[key]["somewhat_prefer_enriched"],
                    st.session_state.detailed_quiz_results[key]["completely_prefer_enriched"]
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
                    st.info("Overall, you have a strong preference for original statements. You might prefer clearer, more concise language.")
                elif overall_tendency < -0.5:
                    st.info("Overall, you have a moderate preference for original statements. You seem to value clarity and directness.")
                elif overall_tendency < 0:
                    st.info("Overall, you have a slight preference for original statements, but you also appreciate some personalization.")
                elif overall_tendency == 0:
                    st.info("Overall, you have no strong preference between original and personalized statements.")
                elif overall_tendency < 0.5:
                    st.info("Overall, you have a slight preference for personalized statements, but you also value clarity.")
                elif overall_tendency < 1:
                    st.info("Overall, you have a moderate preference for personalized statements. You appreciate context and detail.")
                else:
                    st.info("Overall, you have a strong preference for personalized statements. You value detailed, contextual information.")
            
        # Option to reset quiz
        if st.button("Reset Quiz Results"):
            st.session_state.quiz_results = {"original": 0, "enriched": 0}
            st.session_state.detailed_quiz_results = {
                "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
            }
            st.session_state.quiz_shown_indices = []
            
            # Save reset quiz results to database
            save_quiz_results(
                st.session_state.user["id"],
                0, 0,
                st.session_state.detailed_quiz_results
            )
            
            st.success("Quiz results have been reset!")
            st.rerun()
        
        return
    
    # Select a random statement
    statement_idx = np.random.choice(available_indices)
    statement_pair = st.session_state.enriched_statements[statement_idx]
    
    # Randomly decide which statement to show first
    first_is_original = np.random.random() > 0.5
    
    if first_is_original:
        statement_a = statement_pair["original"]
        statement_b = statement_pair["enriched"]
    else:
        statement_a = statement_pair["enriched"]
        statement_b = statement_pair["original"]
    
    # Display the statements
    st.subheader("Compare these statements:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Statement A")
        st.info(statement_a)
        
    with col2:
        st.markdown("### Statement B")
        st.success(statement_b)
    
    # Create form for evaluation
    with st.form("quiz_form"):
        st.markdown("### Evaluate the statements on these criteria:")
        
        # Create a dictionary to store responses
        responses = {}
        
        # Define the criteria
        criteria = {
            "understand": "Which statement is easier to understand?",
            "read": "Which statement is easier to read?",
            "detail": "Which statement offers greater detail?",
            "profession": "Which statement fits your profession better?",
            "assessment": "Which statement is more helpful for a self-assessment?"
        }
        
        # Create radio buttons for each criterion
        for key, question in criteria.items():
            responses[key] = st.radio(
                question,
                ["Completely Prefer A", "Somewhat Prefer A", "Neither", "Somewhat Prefer B", "Completely Prefer B"],
                horizontal=True,
                key=f"quiz_{key}_{statement_idx}",
                index=None  # Set index to None to have no default selection
            )
        
        # Submit button
        submitted = st.form_submit_button("Submit Evaluation")
        
        if submitted:
            # Process responses
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
            if average_score > 0:
                st.session_state.quiz_results["original"] += 1
            elif average_score < 0:
                st.session_state.quiz_results["enriched"] += 1
            else:
                # If exactly 0, randomly assign to break ties
                if np.random.random() > 0.5:
                    st.session_state.quiz_results["original"] += 1
                else:
                    st.session_state.quiz_results["enriched"] += 1
            
            # Save quiz results to database after each submission
            save_quiz_results(
                st.session_state.user["id"],
                st.session_state.quiz_results["original"],
                st.session_state.quiz_results["enriched"],
                st.session_state.detailed_quiz_results
            )
            
            # Add to shown indices
            st.session_state.quiz_shown_indices.append(statement_idx)
            
            # Rerun to show the next question
            st.rerun() 