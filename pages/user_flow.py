import streamlit as st
import numpy as np
import plotly.graph_objects as go
from pages.profile_builder import display_profile_builder
from pages.quiz import display_quiz
from services.statement_service import get_statements_from_settings
from services.enrichment_service import enrich_statement_with_llm
from services.metrics_service import calculate_quality_metrics
from services.db.crud._profiles import save_profile, get_profile
from services.db.crud._quiz import save_quiz_results, get_quiz_results, get_quiz_results_list
from services.db.crud._statements import get_user_statements

def display_user_flow():
    st.title("🚶 User Journey")
    
    # Initialize flow state if not exists
    if 'flow_step' not in st.session_state:
        st.session_state.flow_step = 1
    
    # Try to load existing profile from database
    if 'profile' not in st.session_state:
        db_profile = get_profile(st.session_state.user["id"])
        if db_profile:
            st.session_state.profile = db_profile
    
    # Try to load existing quiz results from database
    if 'quiz_results' not in st.session_state:
        db_quiz_results_list = get_quiz_results_list(st.session_state.user["id"])
        if db_quiz_results_list:
            # Initialize with empty results for new attempt
            st.session_state.quiz_results = {"original": 0, "enriched": 0}
            st.session_state.detailed_quiz_results = {
                "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
            }
            st.session_state.previous_quiz_results = db_quiz_results_list
            st.session_state.has_previous_results = True
        else:
            st.session_state.has_previous_results = False
    
    # Load user statements from database
    if 'enriched_statements' not in st.session_state:
        user_statements = get_user_statements(st.session_state.user["id"])
        if user_statements:
            st.session_state.enriched_statements = user_statements
    
    # Display progress bar
    steps = ["Profile", "Quiz", "Results"]
    current_step = st.session_state.flow_step
    
    # Calculate progress percentage
    progress = (current_step - 1) / (len(steps) - 1) if len(steps) > 1 else 1.0
    
    # Display progress bar and step indicator
    st.progress(progress)
    
    # Display step indicators
    cols = st.columns(len(steps))
    for i, (col, step) in enumerate(zip(cols, steps)):
        step_num = i + 1
        if step_num < current_step:
            col.markdown(f"### ✅ {step}")
        elif step_num == current_step:
            col.markdown(f"### 🔵 {step}")
        else:
            col.markdown(f"### ⚪ {step}")
    
    st.markdown("---")
    
    # Step 1: Profile Builder
    if st.session_state.flow_step == 1:
        st.subheader("Step 1: Create Your Profile")
        st.markdown("""
        First, let's create your digital skills profile. This information will be used to personalize
        statements and provide tailored feedback.
        """)
        
        # Use the existing profile builder with a custom submit handler
        with st.form("flow_profile_form"):
            col1, col2 = st.columns(2)

            with col1:
                job_role = st.text_input("Job Role", value=st.session_state.profile.get("job_role", ""))
                job_domain = st.text_input("Job Domain", value=st.session_state.profile.get("job_domain", ""))
                years_experience = st.number_input("Years of Experience", min_value=0, max_value=50,
                                                   value=st.session_state.profile.get("years_experience", 0))

            with col2:
                digital_proficiency = st.select_slider(
                    "Digital Proficiency",
                    options=["Beginner", "Intermediate", "Advanced", "Expert"],
                    value=st.session_state.profile.get("digital_proficiency", "Intermediate")
                )
                primary_tasks = st.text_area("Primary Tasks", value=st.session_state.profile.get("primary_tasks", ""))

            submit_button = st.form_submit_button("Save Profile & Continue")

            if submit_button:
                # Validate that required fields are filled
                if not job_role or not job_domain or not primary_tasks:
                    st.error("Please fill in all required fields.")
                else:
                    # Create profile data dictionary
                    profile_data = {
                        "job_role": job_role,
                        "job_domain": job_domain,
                        "years_experience": years_experience,
                        "digital_proficiency": digital_proficiency,
                        "primary_tasks": primary_tasks
                    }
                    
                    # Save to database
                    if save_profile(st.session_state.user["id"], profile_data):
                        st.session_state.profile = profile_data
                        st.session_state.flow_step = 2
                        st.rerun()
                    else:
                        st.error("Failed to save profile to database. Please try again.")
    
    # Step 2: Quiz
    elif st.session_state.flow_step == 2:
        st.subheader("Step 2: Statement Preference Quiz")
        
        # Check if we have enriched statements
        if len(st.session_state.enriched_statements) < 1:
            
            # Generate some sample enriched statements for testing
            if st.button("Let's start the quiz"):
                # Get statements based on user settings
                sample_statements = get_statements_from_settings()
                
                # Limit to max statements per quiz from settings
                max_statements = 3  # Default
                if 'user_settings' in st.session_state and 'max_statements_per_quiz' in st.session_state.user_settings:
                    max_statements = st.session_state.user_settings["max_statements_per_quiz"]
                
                # Take only the first max_statements
                sample_statements = sample_statements[:max_statements]
                
                # Create context from profile
                context = ", ".join(
                    [f"{k.replace('_', ' ').title()}: {v}" for k, v in st.session_state.profile.items() if v])
                
                # Enrich statements
                with st.spinner("Generating sample statements..."):
                    for statement in sample_statements:
                        enriched = enrich_statement_with_llm(context, statement, 150)
                        metrics = calculate_quality_metrics(statement, enriched)
                        
                        st.session_state.enriched_statements.append({
                            "original": statement,
                            "enriched": enriched,
                            "metrics": metrics
                        })
                
                st.success(f"Generated {len(sample_statements)} statements! You can now take the quiz.")
                st.rerun()
        else:
            # Custom quiz implementation for the flow
            # Select a random statement that hasn't been shown in the quiz yet
            if 'quiz_shown_indices' not in st.session_state:
                st.session_state.quiz_shown_indices = []
                
            available_indices = [i for i in range(len(st.session_state.enriched_statements)) 
                                if i not in st.session_state.quiz_shown_indices]
            
            if not available_indices:
                # All statements have been shown, move to results
                st.session_state.flow_step = 3
                st.rerun()
            else:
                # Select a random statement
                statement_idx = np.random.choice(available_indices)
                statement_pair = st.session_state.enriched_statements[statement_idx]
                
                # Create a unique key for this quiz iteration to ensure form elements reset
                if 'current_quiz_iteration' not in st.session_state:
                    st.session_state.current_quiz_iteration = 0
                else:
                    st.session_state.current_quiz_iteration += 1
                
                quiz_iteration_key = f"quiz_iteration_{st.session_state.current_quiz_iteration}"
                
                # Randomize the order of presentation
                if np.random.random() > 0.5:
                    first_statement = statement_pair["original"]
                    second_statement = statement_pair["enriched"]
                    first_is_original = True
                else:
                    first_statement = statement_pair["enriched"]
                    second_statement = statement_pair["original"]
                    first_is_original = False
                    
                st.markdown("Compare these two statements and select your preferences:")
                
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
                with st.form("flow_preference_form"):
                    # Store the responses
                    responses = {}
                    
                    # Create sliders for each criterion
                    for key, question in criteria.items():
                        # Используем уникальный ключ для каждого слайдера, включающий индекс итерации
                        slider_key = f"{quiz_iteration_key}_{key}"
                        responses[key] = st.select_slider(
                            question,
                            options=["Completely Prefer A", "Somewhat Prefer A", "Neither", "Somewhat Prefer B", "Completely Prefer B"],
                            value=None,
                            key=slider_key
                        )
                    
                    # Progress indicator
                    total_statements = min(10, len(st.session_state.enriched_statements))  # Limit to 5 statements max
                    completed = len(st.session_state.quiz_shown_indices)
                    progress_percentage = completed / total_statements * 100
                    
                    st.progress(progress_percentage / 100, f"{progress_percentage:.0f}% ({completed}/{total_statements})")
                    
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
                    
                    # Check if we've shown enough statements (limit to max from settings)
                    max_statements = 5  # Default
                    if 'user_settings' in st.session_state and 'max_statements_per_quiz' in st.session_state.user_settings:
                        max_statements = st.session_state.user_settings["max_statements_per_quiz"]
                        
                    if len(st.session_state.quiz_shown_indices) >= min(max_statements, len(st.session_state.enriched_statements)):
                        st.session_state.flow_step = 3
                    
                    # Save quiz results to database after each submission
                    save_quiz_results(
                        st.session_state.user["id"],
                        st.session_state.quiz_results["original"],
                        st.session_state.quiz_results["enriched"],
                        st.session_state.detailed_quiz_results
                    )
                    
                    # Update the list of previous results
                    st.session_state.previous_quiz_results = get_quiz_results_list(st.session_state.user["id"])
                    st.session_state.has_previous_results = True
                    
                    # Rerun to show the next question or move to results
                    st.rerun()
    
    # Step 3: Results
    elif st.session_state.flow_step == 3:
        st.subheader("Step 3: Your Results")
        
        # Add dropdown for selecting previous results if they exist
        selected_result = None
        if st.session_state.has_previous_results:
            st.markdown("### View Previous Results")
            result_options = [f"Attempt {i+1}" for i in range(len(st.session_state.previous_quiz_results))]
            result_options.append("Current Attempt")
            selected_attempt = st.selectbox("Select attempt to view:", result_options)
            
            if selected_attempt != "Current Attempt":
                attempt_index = int(selected_attempt.split()[-1]) - 1
                selected_result = st.session_state.previous_quiz_results[attempt_index]
        
        # Use either selected previous result or current results
        display_results = selected_result if selected_result else {
            "original": st.session_state.quiz_results["original"],
            "enriched": st.session_state.quiz_results["enriched"],
            "detailed_results": st.session_state.detailed_quiz_results
        }

        total_responses = display_results["original"] + display_results["enriched"]
        
        if total_responses == 0:
            st.warning("No quiz results available. Please complete the quiz first.")
        else:
            st.success("Congratulations! You've completed the assessment.")
            
            # Display results summary
            st.markdown("### Your Statement Preferences")
            
            original_percentage = (display_results["original"] / total_responses) * 100
            enriched_percentage = (display_results["enriched"] / total_responses) * 100
            
            # Create interactive pie chart with Plotly
            labels = ["Original Statements", "Personalized Statements"]
            values = [display_results["original"], display_results["enriched"]]
            
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
                    'text': "Overall Statement Preference",
                    'y':0.95,
                    'x':0.5,
                    'xanchor': 'center',
                    'yanchor': 'top'
                },
                height=400,
                margin=dict(t=50, b=0, l=0, r=0)
            )
            
            # Display the chart
            st.plotly_chart(fig, use_container_width=True)
            
            # Display detailed results by criteria
            st.markdown("### Detailed Results by Criteria")
            
            # Create tabs for each criterion
            criteria_keys = ["understand", "read", "detail", "profession", "assessment"]
            criteria_names = ["Understanding", "Readability", "Detail", "Professional Relevance", "Self-Assessment"]
            
            detailed_tabs = st.tabs(criteria_names)
            
            # Calculate overall tendency
            overall_tendency = 0
            total_weights = 0
            
            for i, (tab, key) in enumerate(zip(detailed_tabs, criteria_keys)):
                with tab:
                    values = [
                        display_results["detailed_results"][key]["completely_prefer_original"],
                        display_results["detailed_results"][key]["somewhat_prefer_original"],
                        display_results["detailed_results"][key]["neither"],
                        display_results["detailed_results"][key]["somewhat_prefer_enriched"],
                        display_results["detailed_results"][key]["completely_prefer_enriched"]
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
                        
                        # Add bars
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
                        elif tendency < 0:
                            tendency_text = "Slight preference for original"
                        elif tendency == 0:
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
                        
                        # Update layout
                        detail_fig.update_layout(
                            title=criteria_names[i],
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
                        
                        st.plotly_chart(detail_fig, use_container_width=True)
                    else:
                        st.info(f"No data available for {criteria_names[i]} yet.")
            
            # Calculate overall tendency if we have data
            if total_weights > 0:
                overall_tendency = overall_tendency / total_weights
                
                # Display overall interpretation
                st.subheader("Overall Interpretation")
                
                if overall_tendency < -1:
                    st.info("You strongly prefer original statements overall.")
                elif overall_tendency < -0.2:
                    st.info("You somewhat prefer original statements overall.")
                elif overall_tendency <= 0.2:
                    st.info("You have no strong preference between original and personalized statements.")
                elif overall_tendency < 1:
                    st.info("You somewhat prefer personalized statements overall.")
                else:
                    st.info("You strongly prefer personalized statements overall.")
            
            # Option to restart the quiz
            if st.button("Restart Assessment"):
                # Reset quiz results in both session and database
                st.session_state.quiz_results = {"original": 0, "enriched": 0}
                st.session_state.detailed_quiz_results = {
                    "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                    "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                    "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                    "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
                    "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
                }
                save_quiz_results(
                    st.session_state.user["id"],
                    0, 0,
                    st.session_state.detailed_quiz_results
                )
                st.session_state.quiz_shown_indices = []
                st.session_state.flow_step = 1
                st.rerun() 