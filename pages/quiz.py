import streamlit as st
import numpy as np
import plotly.graph_objects as go

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
                    st.info("Overall, you show a strong preference for personalized statements across most criteria.")
                elif overall_tendency < -0.5:
                    st.info("Overall, you show a moderate preference for personalized statements.")
                elif overall_tendency < 0:
                    st.info("Overall, you show a slight preference for personalized statements.")
                elif overall_tendency == 0:
                    st.info("Overall, you show no clear preference between original and personalized statements.")
                elif overall_tendency < 0.5:
                    st.info("Overall, you show a slight preference for original statements.")
                elif overall_tendency < 1:
                    st.info("Overall, you show a moderate preference for original statements.")
                else:
                    st.info("Overall, you show a strong preference for original statements across most criteria.")
        
        # Option to reset quiz
        if st.button("Reset Quiz"):
            st.session_state.quiz_shown_indices = []
            st.session_state.quiz_results = {"original": 0, "enriched": 0}
            st.session_state.detailed_quiz_results = {
                "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
            }
            st.rerun()
            
        st.stop()
        
    # Select a random statement
    statement_idx = np.random.choice(available_indices)
    statement_pair = st.session_state.enriched_statements[statement_idx]
    
    # Randomize the order of presentation
    if np.random.random() > 0.5:
        first_statement = statement_pair["original"]
        second_statement = statement_pair["enriched"]
        first_is_original = True
    else:
        first_statement = statement_pair["enriched"]
        second_statement = statement_pair["original"]
        first_is_original = False
        
    st.subheader("Select your preferred statement:")
    
    # Display the statements side by side
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### A")
        st.info(first_statement)
        
    with col2:
        st.markdown("### B")
        st.info(second_statement)
        
    # Add a divider
    st.markdown("---")
    
    # Create the detailed preference form
    st.markdown("### Your Preference")
    
    # Define the criteria questions
    criteria = {
        "understand": "Which statement is easier to understand?",
        "read": "Which statement is easier to read?",
        "detail": "Which statement offers greater detail?",
        "profession": "Which statement fits your profession?",
        "assessment": "Which statement is helpful for a self-assessment?"
    }
    
    # Create a form for all criteria
    with st.form("preference_form"):
        # Store the responses
        responses = {}
        
        # Create sliders for each criterion
        for key, question in criteria.items():
            responses[key] = st.select_slider(
                question,
                options=["Completely Prefer A", "Somewhat Prefer A", "Neither", "Somewhat Prefer B", "Completely Prefer B"],
                value="Neither"
            )
        
        # Progress indicator
        total_statements = len(st.session_state.enriched_statements)
        completed = len(st.session_state.quiz_shown_indices)
        progress_percentage = completed / total_statements * 100
        
        st.progress(progress_percentage / 100, f"{progress_percentage:.0f}%")
        
        # Submit button
        submitted = st.form_submit_button("Submit and Continue")
        
    if submitted:
        # Process the responses
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
        
        # Add to shown indices
        st.session_state.quiz_shown_indices.append(statement_idx)
        
        # Rerun to show the next question
        st.rerun() 