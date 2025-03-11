import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Import service functions
from service import (
    load_llm, 
    load_embedding_model, 
    enrich_statement_with_llm, 
    calculate_quality_metrics, 
    generate_chat_response,
    get_sample_statements
)

# Import page display functions
from pages.home import display_home_page

def run_app():
    # Debug information
    print("DEBUG: Starting run_app() function")
    
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = {
            "id": 1,
            "username": "demo_user",
            "role": "user"
        }
        print("DEBUG: Initialized user session state")

    if 'profile' not in st.session_state:
        st.session_state.profile = {
            "job_role": "Frontend developer",
            "job_domain": "IT Development",
            "years_experience": 4,
            "digital_proficiency": "Intermediate",
            "primary_tasks": "Working with Figma, creating responsive SCSS styles and creating components in Angular"
        }

    if 'enriched_statements' not in st.session_state:
        st.session_state.enriched_statements = []
        
    if 'quiz_results' not in st.session_state:
        st.session_state.quiz_results = {"original": 0, "enriched": 0}

    # Add detailed quiz results structure
    if 'detailed_quiz_results' not in st.session_state:
        st.session_state.detailed_quiz_results = {
            "understand": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "read": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "detail": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "profession": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0},
            "assessment": {"completely_prefer_original": 0, "somewhat_prefer_original": 0, "neither": 0, "somewhat_prefer_enriched": 0, "completely_prefer_enriched": 0}
        }

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Get sample statements
    sample_statements = get_sample_statements()

    # Sidebar navigation
    st.sidebar.title("DigiBot Demo")
    page = st.sidebar.radio(
        "Navigation",
        ["Home", "Profile Builder", "Enrichment Demo", "Batch Enrichment", "Quiz", "Chatbot", "Analytics"]
    )

    # Home page
    if page == "Home":
        display_home_page()

    # Profile Builder page
    elif page == "Profile Builder":
        display_profile_builder()

    # Enrichment Demo page
    elif page == "Enrichment Demo":
        display_enrichment_demo(sample_statements)

    # Batch Enrichment page
    elif page == "Batch Enrichment":
        display_batch_enrichment(sample_statements)
    
    # Quiz page
    elif page == "Quiz":
        display_quiz()

    # Chatbot page
    elif page == "Chatbot":
        display_chatbot()

    # Analytics page
    elif page == "Analytics":
        display_analytics()

    # Add footer
    st.markdown("---")
    st.markdown("DigiBot Demo | Created with Streamlit and LangChain")

# Page display functions
def display_profile_builder():
    st.title("👤 Profile Builder")
    st.markdown("""
    Create your digital skills profile to personalize the DigiBot experience.
    This information will be used to tailor statements and chatbot responses to your specific context.
    """)

    with st.form("profile_form"):
        col1, col2 = st.columns(2)

        with col1:
            job_role = st.text_input("Job Role", value=st.session_state.profile["job_role"])
            job_domain = st.text_input("Job Domain", value=st.session_state.profile["job_domain"])
            years_experience = st.number_input("Years of Experience", min_value=0, max_value=50,
                                               value=st.session_state.profile["years_experience"])

        with col2:
            digital_proficiency = st.select_slider(
                "Digital Proficiency",
                options=["Beginner", "Intermediate", "Advanced", "Expert"],
                value=st.session_state.profile["digital_proficiency"]
            )
            primary_tasks = st.text_area("Primary Tasks", value=st.session_state.profile["primary_tasks"])

        submit_button = st.form_submit_button("Save Profile")

        if submit_button:
            st.session_state.profile = {
                "job_role": job_role,
                "job_domain": job_domain,
                "years_experience": years_experience,
                "digital_proficiency": digital_proficiency,
                "primary_tasks": primary_tasks
            }
            st.success("Profile saved successfully!")
            st.balloons()

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

                # Enrich statement
                print("DEBUG: Calling enrich_statement_with_llm")
                enriched_statement = enrich_statement_with_llm(context, original_statement, statement_length)
                print(f"DEBUG: Received enriched statement: {enriched_statement[:100]}...")

                # Calculate quality metrics
                print("DEBUG: Calculating quality metrics")
                metrics = calculate_quality_metrics(original_statement, enriched_statement)
                print(f"DEBUG: Metrics calculated: {metrics}")

                # Save to session state
                st.session_state.enriched_statements.append({
                    "original": original_statement,
                    "enriched": enriched_statement,
                    "metrics": metrics
                })
                print("DEBUG: Added to session state")

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

def display_batch_enrichment(sample_statements):
    st.title("🔄 Batch Enrichment")
    
    if not st.session_state.profile["job_role"]:
        st.warning("Please create your profile first in the Profile Builder section.")
        st.stop()
        
    st.markdown("""
    Select multiple statements to enrich at once or add your own custom statements.
    """)
    
    # Create multiselect for sample statements
    selected_samples = st.multiselect(
        "Select statements to enrich:",
        sample_statements,
        default=[]
    )
    
    # Option to add custom statements
    st.subheader("Add Custom Statements")
    
    # Initialize custom statements list if not exists
    if 'custom_statements' not in st.session_state:
        st.session_state.custom_statements = [""]
        
    # Display all custom statement inputs
    custom_statements = []
    for i, statement in enumerate(st.session_state.custom_statements):
        col1, col2 = st.columns([5, 1])
        with col1:
            custom_statement = st.text_input(f"Custom statement #{i+1}", value=statement, key=f"custom_{i}")
            if custom_statement:
                custom_statements.append(custom_statement)
        with col2:
            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.custom_statements.pop(i)
                st.rerun()
    
    # Add button for new custom statement
    if st.button("Add Another Custom Statement"):
        st.session_state.custom_statements.append("")
        st.rerun()
        
    # Combine selected sample statements and custom statements
    all_statements = selected_samples + custom_statements
    
    # Statement length slider
    statement_length = st.slider("Statement Length (characters)", 100, 300, 150, key="batch_length")
    
    # Process button
    if st.button("Process All Statements") and all_statements:
        with st.spinner("Processing statements..."):
            # Create context from profile
            context = ", ".join(
                [f"{k.replace('_', ' ').title()}: {v}" for k, v in st.session_state.profile.items() if v])
            
            progress_bar = st.progress(0)
            
            # Process each statement
            for i, statement in enumerate(all_statements):
                try:
                    # Update progress
                    progress = (i + 1) / len(all_statements)
                    progress_bar.progress(progress)
                    
                    # Enrich statement
                    enriched_statement = enrich_statement_with_llm(context, statement, statement_length)
                    
                    # Calculate metrics
                    metrics = calculate_quality_metrics(statement, enriched_statement)
                    
                    # Save to session state
                    st.session_state.enriched_statements.append({
                        "original": statement,
                        "enriched": enriched_statement,
                        "metrics": metrics
                    })
                    
                except Exception as e:
                    st.error(f"Error processing statement '{statement[:30]}...': {str(e)}")
            
            st.success(f"Processed {len(all_statements)} statements successfully!")
            
        # Display summary
        st.subheader("Summary of Processed Statements")
        for i, item in enumerate(st.session_state.enriched_statements[-len(all_statements):]):
            with st.expander(f"Statement {i+1}: {item['original'][:50]}..."):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Original:**")
                    st.info(item['original'])
                with col2:
                    st.markdown("**Enriched:**")
                    st.success(item['enriched'])
                
                # Display metrics
                st.markdown("**Metrics:**")
                metrics_cols = st.columns(3)
                with metrics_cols[0]:
                    st.metric("TF-IDF Similarity", f"{item['metrics']['cosine_tfidf']:.2f}")
                with metrics_cols[1]:
                    st.metric("Embedding Similarity", f"{item['metrics']['cosine_embedding']:.2f}")
                with metrics_cols[2]:
                    st.metric("Reading Ease", f"{item['metrics']['readability']['estimated_reading_ease']:.1f}")

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

def display_chatbot():
    st.title("💬 Digital Skills Chatbot")
    
    if not st.session_state.profile["job_role"]:
        st.warning("Please create your profile first in the Profile Builder section.")
        st.stop()
        
    st.markdown("""
    Chat with DigiBot about digital skills, competencies, and learning resources.
    The chatbot is personalized based on your profile.
    """)
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Get user input - исправленная версия
    prompt = st.chat_input("Ask about digital skills...")
    
    if prompt:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = generate_chat_response(prompt, st.session_state.profile)
                    st.markdown(response)
                    
                    # Add assistant response to chat history
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_message = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_message)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_message})
        
        # Rerun to update the chat interface
        st.rerun()

def display_analytics():
    st.title("📊 Analytics Dashboard")
    
    if len(st.session_state.enriched_statements) < 1:
        st.warning("No enriched statements available for analysis.")
        st.info("Go to the Enrichment Demo or Batch Enrichment page to create more statements.")
        st.stop()
        
    # Prepare data for visualization
    data = []
    for i, item in enumerate(st.session_state.enriched_statements):
        data.append({
            "id": i + 1,
            "original": item["original"],
            "enriched": item["enriched"],
            "original_length": len(item["original"]),
            "enriched_length": len(item["enriched"]),
            "tfidf_similarity": item["metrics"]["cosine_tfidf"],
            "embedding_similarity": item["metrics"]["cosine_embedding"],
            "reading_ease": item["metrics"]["readability"]["estimated_reading_ease"],
            "word_count": item["metrics"]["readability"]["word_count"],
            "avg_word_length": item["metrics"]["readability"]["avg_word_length"]
        })
    
    df = pd.DataFrame(data)
    
    # Create tabs for different visualizations
    viz_tabs = st.tabs(["Overview", "Statement Comparison", "Quiz Results"])
    
    with viz_tabs[0]:
        # Overview metrics
        st.subheader("Overview Metrics")
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Statements", len(df))
            
        with col2:
            avg_similarity = df["embedding_similarity"].mean()
            st.metric("Avg. Embedding Similarity", f"{avg_similarity:.2f}")
            
        with col3:
            avg_reading_ease = df["reading_ease"].mean()
            st.metric("Avg. Reading Ease", f"{avg_reading_ease:.1f}")
        
        # Create a correlation heatmap
        st.subheader("Correlation Matrix")
        
        # Select numeric columns for correlation
        numeric_cols = ["original_length", "enriched_length", "tfidf_similarity", 
                        "embedding_similarity", "reading_ease", "word_count", "avg_word_length"]
        
        corr_matrix = df[numeric_cols].corr()
        
        # Create a heatmap using Plotly
        fig = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="RdBu_r",
            title="Correlation Between Metrics"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Length comparison
        st.subheader("Statement Length Comparison")
        
        # Create a scatter plot
        fig = px.scatter(
            df,
            x="original_length",
            y="enriched_length",
            size="embedding_similarity",
            color="reading_ease",
            hover_name="id",
            labels={
                "original_length": "Original Length (chars)",
                "enriched_length": "Enriched Length (chars)",
                "embedding_similarity": "Embedding Similarity",
                "reading_ease": "Reading Ease"
            },
            title="Original vs. Enriched Statement Length"
        )
        
        # Add a diagonal line for reference
        fig.add_shape(
            type="line",
            x0=min(df["original_length"]),
            y0=min(df["original_length"]),
            x1=max(df["original_length"]),
            y1=max(df["original_length"]),
            line=dict(color="gray", dash="dash")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    with viz_tabs[1]:
        # Statement comparison
        st.subheader("Statement Comparison")
        selected_id = st.selectbox("Select a statement to view details:", df["id"].tolist())

        if selected_id:
            idx = selected_id - 1
            selected_item = st.session_state.enriched_statements[idx]

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Original Statement")
                st.info(selected_item["original"])

            with col2:
                st.markdown("### Enriched Statement")
                st.success(selected_item["enriched"])

            # Display detailed metrics
            st.markdown("### Detailed Metrics")
            metrics_df = pd.DataFrame([{
                "Metric": key,
                "Value": value
            } for key, value in selected_item["metrics"]["readability"].items()])

            st.dataframe(metrics_df)
            
    with viz_tabs[2]:
        # Quiz results visualization
        st.subheader("Quiz Preference Results")
        
        total_responses = st.session_state.quiz_results["original"] + st.session_state.quiz_results["enriched"]
        
        if total_responses == 0:
            st.info("No quiz results available yet. Take the quiz to see your preferences.")
        else:
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
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Create detailed analysis charts
            st.subheader("Detailed Analysis by Criteria")
            
            # Define criteria names
            criteria_names = {
                "understand": "Which statement is easier to understand?",
                "read": "Which statement is easier to read?",
                "detail": "Which statement offers greater detail?",
                "profession": "Which statement fits your profession?",
                "assessment": "Which statement is helpful for a self-assessment?"
            }
            
            # Create a 2x3 grid for the detailed charts
            detailed_tabs = st.tabs(["Understanding", "Readability", "Detail", "Professional Fit", "Self-Assessment"])
            
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
                    
                    st.plotly_chart(fig, use_container_width=True)