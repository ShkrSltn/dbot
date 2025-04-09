import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from services.db.crud._quiz import get_quiz_results_list
from services.db.crud._settings import get_competency_questions_enabled

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
        else:
            # Инициализировать как пустой список, а не None
            st.session_state.previous_quiz_results = []
        has_previous_results = st.session_state.has_previous_results
    
    # Убедимся, что previous_quiz_results - всегда список, даже если пустой
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
                    # Если есть время обновления и оно отличается от времени создания, показываем его
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
        
        # Добавим отображение даты создания и обновления, если они есть
        created_at = display_results.get("created_at")
        updated_at = display_results.get("updated_at")
        
        if created_at and not isinstance(created_at, str):
            st.caption(f"Created: {created_at.strftime('%Y-%m-%d %H:%M')}")
            
            # Показываем дату обновления только если она отличается от даты создания
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
        # Проверяем настройку показа компетенций
        show_competency_tab = get_competency_questions_enabled()

        # Создаем вкладки в зависимости от настройки
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
            # Показываем только одну вкладку с предпочтениями
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

def display_competency_results(display_results):
    """Display the competency assessment results using pie charts"""
    
    competency_results = display_results.get("competency_results", [])
    
    if not competency_results:
        st.info("No competency assessment data available for this attempt.")
        return
    
    st.markdown("### Your Digital Competency Self-Assessment")
    
    # Create a dataframe for the competency results
    comp_data = []
    for comp in competency_results:
        comp_data.append({
            "Category": comp.get("category", "Unknown"),
            "Subcategory": comp.get("subcategory", "Unknown"),
            "Statement": comp.get("statement", ""),
            "Competency": comp.get("competency", "Intermediate")
        })
    
    if not comp_data:
        st.info("No competency assessment data available.")
        return
    
    # Create a DataFrame
    df = pd.DataFrame(comp_data)
    
    # Map from responses to levels - должен обрабатывать как длинные, так и короткие форматы
    response_to_level = {
        "I have no knowledge of this / I never heard of this": "No knowledge",
        "I have only a limited understanding of this and need more explanations": "Basic",
        "I have a good understanding of this": "Intermediate",
        "I fully master this topic/issue and I could explain it to others": "Advanced",
        # Добавляем короткие форматы для обратной совместимости
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
    
    # Calculate competency percentages at each level
    # For statements (base level)
    total_statements = len(df)
    statement_max_score = total_statements * 5  # Max possible score if all were 'Expert'
    statement_score = df["Competency_Value"].sum()
    
    # For subcategories
    subcategory_scores = df.groupby("Subcategory")["Competency_Value"].agg(["mean", "count"]).reset_index()
    subcategory_scores["score_percentage"] = (subcategory_scores["mean"] / 5) * 100  # Convert to percentage
    
    # For categories
    category_scores = df.groupby("Category")["Competency_Value"].agg(["mean", "count"]).reset_index()
    category_scores["score_percentage"] = (category_scores["mean"] / 5) * 100  # Convert to percentage
    
    # Overall competency percentage
    overall_score_percentage = (df["Competency_Value"].mean() / 5) * 100
    
    # Create the digital competence visualization with horizontal bars for categories
    st.subheader("Digital Competence")
    
    # Create horizontal progress bars for each category
    for i, row in category_scores.iterrows():
        category = row["Category"]
        percentage = row["score_percentage"]
        
        # Define colors based on category
        colors = {
            "Information and data literacy": "#3498db",  # Blue
            "Communication and collaboration": "#e74c3c",  # Red
            "Digital content creation": "#f1c40f",  # Yellow
            "Safety": "#2ecc71",  # Green
            "Problem solving": "#e67e22"   # Orange
        }
        
        color = colors.get(category, "#3498db")
        
        # Create container with background color - using rgba for transparency in HTML
        container_html = f"""
        <div style="background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2); padding: 10px; border-radius: 5px; margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 3;">{category}</div>
                <div style="flex: 7; background-color: #f0f0f0; height: 30px; border-radius: 15px; position: relative;">
                    <div style="position: absolute; width: {percentage}%; height: 100%; background-color: {color}; border-radius: 15px; display: flex; align-items: center; justify-content: center;">
                        <span style="color: white; font-weight: bold;">{percentage:.0f}%</span>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(container_html, unsafe_allow_html=True)
    
    # Create main pie chart with subcategories and their percentages
    # Group by subcategory and calculate average competency
    subcategory_data = df.groupby(["Category", "Subcategory"])["Competency_Value"].mean().reset_index()
    subcategory_data["Percentage"] = (subcategory_data["Competency_Value"] / 5) * 100
    
    # Define colors for each category
    color_map = {
        "Information and data literacy": "#3498db",  # Blue
        "Communication and collaboration": "#e74c3c",  # Red
        "Digital content creation": "#f1c40f",  # Yellow
        "Safety": "#2ecc71",  # Green
        "Problem solving": "#e67e22"   # Orange
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
        hole=0.3,  # Creates a donut chart
        marker=dict(
            colors=subcategory_colors,
            line=dict(color='#FFFFFF', width=2)
        ),
        textinfo='label+percent',
        textposition='outside',
        insidetextorientation='radial',
        textfont=dict(size=10),
        hoverinfo='label+value+percent',
        hovertemplate='<b>%{label}</b><br>Score: %{value:.1f}%<extra></extra>'
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
            'text': "Competency by Subcategory",
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
        st.session_state.quiz_results = {"original": 0, "enriched": 0, "neither": 0}
        st.session_state.statement_preferences = []  # Reset statement preferences
        st.session_state.detailed_quiz_results = {
            "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
        }
        st.session_state.competency_results = []  # Reset competency results
        st.session_state.quiz_shown_indices = []
        st.session_state.flow_step = 1
        st.rerun()
