import streamlit as st
import plotly.graph_objects as go
from services.db.crud._quiz import get_quiz_results_list

def display_results_step():
    st.subheader("Step 3: Your Results")
    
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
        has_previous_results = st.session_state.has_previous_results
    
    if has_previous_results and 'previous_quiz_results' in st.session_state:
        st.markdown("### View Previous Results")
        
        # Create a more descriptive list of attempts with timestamps if available
        result_options = []
        for i, result in enumerate(st.session_state.previous_quiz_results):
            timestamp = result.get("created_at", "")
            if timestamp:
                # Format timestamp if it exists
                if isinstance(timestamp, str):
                    attempt_label = f"Attempt {i+1} ({timestamp})"
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
    elif 'quiz_results' in st.session_state:
        display_results = {
            "original": st.session_state.quiz_results.get("original", 0),
            "enriched": st.session_state.quiz_results.get("enriched", 0),
            "neither": st.session_state.quiz_results.get("neither", 0),
            "detailed_results": st.session_state.get("detailed_quiz_results", {})
        }
    else:
        display_results = {"original": 0, "enriched": 0, "neither": 0, "detailed_results": {}}

    # Check if there are any responses (including "neither")
    total_responses = display_results.get("original", 0) + display_results.get("enriched", 0) + display_results.get("neither", 0)
    
    if total_responses == 0:
        st.warning("No quiz results available for this attempt. Please complete the quiz first.")
        
        # If user has no results at all, offer to start the assessment
        if not has_previous_results:
            if st.button("Start Assessment"):
                reset_quiz_session_state()
                st.session_state.flow_step = 1
                st.rerun()
    else:
        # Pass the selected results to the display functions
        display_results_summary(display_results, total_responses)
        display_detailed_results(display_results)
        display_restart_option()

def reset_quiz_session_state():
    """Reset all quiz-related session state variables"""
    # Reset quiz results
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
    
    # Recalculate total responses to include "neither"
    total_responses = original_count + enriched_count + neither_count
    
    if total_responses == 0:
        st.warning("No responses recorded.")
        return
    
    original_percentage = (original_count / total_responses) * 100
    enriched_percentage = (enriched_count / total_responses) * 100
    neither_percentage = (neither_count / total_responses) * 100
    
    # Create interactive pie chart with Plotly
    labels = ["Original Statements", "Personalized Statements", "No Preference"]
    values = [original_count, enriched_count, neither_count]
    
    # Define colors
    colors = ['#3498db', '#ff7675', '#95a5a6']
    
    # Create figure
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.4,  # Creates a donut chart
        marker=dict(colors=colors),
        textinfo='label+percent',
        textposition='outside',
        pull=[0.1 if original_percentage > max(enriched_percentage, neither_percentage) else 0, 
              0.1 if enriched_percentage > max(original_percentage, neither_percentage) else 0,
              0.1 if neither_percentage > max(original_percentage, neither_percentage) else 0],
        hoverinfo='label+value+percent',
        # Improve text positioning to avoid overlaps
        insidetextorientation='radial'
    )])
    
    # Update layout with improved spacing and positioning
    fig.update_layout(
        title={
            'text': "Overall Statement Preference",
            'y':0.99,
            'x':0.15,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        height=600,  # Further increase height for better spacing
        margin=dict(t=80, b=100, l=80, r=80),  # Increase margins all around
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,  # Position legend further below the chart
            xanchor="center",
            x=0.5
        ),
        # Improve text positioning
        uniformtext_minsize=12,
        uniformtext_mode='hide',
        # Add more space between labels and chart
        annotations=[
            dict(
                x=0.5,
                y=-0.1,
                text="",  # Spacer annotation
                showarrow=False,
                xref="paper",
                yref="paper"
            )
        ]
    )
    
    # Display the chart with a unique key
    st.plotly_chart(fig, use_container_width=True, key="summary_pie_chart")

def display_detailed_results(display_results):
    # Display detailed results by criteria
    st.markdown("### Detailed Results by Criteria")
    
    # Define criteria
    criteria_keys = ["understand", "read", "detail", "profession", "assessment"]
    criteria_names = ["Understanding", "Readability", "Detail", "Professional Relevance", "Self-Assessment"]
    
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
                name = criteria_names[criteria_idx]
                
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
                        elif tendency < -0.1:  # Changed threshold to be more sensitive
                            tendency_text = "Slight preference for original"
                        elif tendency <= 0.1:  # Changed threshold to be more sensitive
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
                                tickfont=dict(size=9)  # Smaller font for x-axis labels
                            ),
                            yaxis=dict(
                                title="Number of Responses"
                            ),
                            height=350,  # Slightly smaller height
                            margin=dict(t=30, b=100, l=30, r=30),  # Adjusted margins
                            font=dict(size=10)  # Smaller font overall
                        )
                        
                        # Add unique key for each plotly chart
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
        
        if overall_tendency < -1:
            st.info("You strongly prefer original statements overall.")
        elif overall_tendency < -0.1:  # Changed threshold to be more sensitive
            st.info("You somewhat prefer original statements overall.")
        elif overall_tendency <= 0.1:  # Changed threshold to be more sensitive
            st.info("You have no strong preference between original and personalized statements.")
        elif overall_tendency < 1:
            st.info("You somewhat prefer personalized statements overall.")
        else:
            st.info("You strongly prefer personalized statements overall.")

def display_restart_option():
    # Option to restart the quiz
    if st.button("Restart Assessment"):
        # Reset quiz results in both session and database
        st.session_state.quiz_results = {"original": 0, "enriched": 0, "neither": 0}
        st.session_state.statement_preferences = []  # Reset statement preferences
        st.session_state.detailed_quiz_results = {
            "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
        }
        st.session_state.quiz_shown_indices = []
        st.session_state.flow_step = 1
        st.rerun()
