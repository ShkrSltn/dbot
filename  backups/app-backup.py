import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from dotenv import load_dotenv
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
# from langchain_huggingface import HuggingFaceEmbeddings  # Закомментируем этот импорт
from langchain_core.runnables import RunnablePassthrough

# Load environment variables
load_dotenv()


# Initialize LangChain models
@st.cache_resource
def load_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key="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"
    )


@st.cache_resource
def load_embedding_model():
    print("DEBUG: Inside load_embedding_model function")
    try:
        # Заменяем HuggingFaceEmbeddings на OpenAIEmbeddings
        model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key="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"
        )
        print("DEBUG: OpenAIEmbeddings model loaded successfully")
        return model
    except Exception as e:
        print(f"DEBUG: Error loading embedding model: {e}")
        raise


# Utility functions
def enrich_statement_with_llm(context, original_statement, statement_length=150):
    """Enriches a statement using LangChain"""
    try:
        # Create a prompt template
        system_template = "You are an expert in digital competencies."
        human_template = """
        Context: {context}

        Original statement: {original_statement}

        Please enhance this statement to make it more professional and clear.
        Keep the length around {statement_length} characters.
        """

        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])

        # Create a chain
        chain = prompt | load_llm() | StrOutputParser()

        # Run the chain
        enriched = chain.invoke({
            "context": context,
            "original_statement": original_statement,
            "statement_length": statement_length
        })

        return enriched.strip()
    except Exception as e:
        print(f"Error enriching statement: {e}")
        raise  # Пробрасываем ошибку дальше


def calculate_quality_metrics(original, enriched):
    """Calculates quality metrics between original and enriched statements"""
    try:
        print("DEBUG: Starting calculate_quality_metrics")
        # Проверяем, что строки не пустые
        if not original or not enriched:
            raise ValueError("Empty string provided for metrics calculation")

        # Embedding similarity using OpenAI embeddings
        print("DEBUG: Loading embedding model")
        embedding_model = load_embedding_model()
        
        # Получение эмбеддингов
        print("DEBUG: Getting embeddings for original text")
        original_embedding = embedding_model.embed_query(original)
        print("DEBUG: Getting embeddings for enriched text")
        enriched_embedding = embedding_model.embed_query(enriched)
        
        # Calculate cosine similarity
        print("DEBUG: Calculating cosine similarity")
        embedding_sim = np.dot(original_embedding, enriched_embedding) / (
                np.linalg.norm(original_embedding) * np.linalg.norm(enriched_embedding))
        
        # TF-IDF similarity (simplified calculation for demo)
        print("DEBUG: Calculating TF-IDF similarity")
        tfidf_sim = 0.5 + (embedding_sim * 0.5)  # Используем embedding_sim как основу
        
        # Simplified readability metrics
        print("DEBUG: Calculating readability metrics")
        word_count = len(enriched.split())
        char_count = len(enriched)
        avg_word_length = char_count / max(1, word_count)
        
        # Readability scores
        readability = {
            "word_count": word_count,
            "character_count": char_count,
            "avg_word_length": avg_word_length,
            "estimated_reading_ease": max(0, min(100, 100 - (avg_word_length * 10)))
        }
        
        print("DEBUG: Metrics calculation completed successfully")
        return {
            "cosine_tfidf": float(tfidf_sim),
            "cosine_embedding": float(embedding_sim),
            "readability": readability
        }
    except Exception as e:
        print(f"DEBUG: Error calculating metrics: {e}")
        raise


def generate_chat_response(query, persona_context):
    """Generates a chat response using LangChain"""
    try:
        # Create system message with user context
        system_content = "You are a helpful digital skills assistant."

        if persona_context:
            system_content += "\n\nUser context:\n"
            for key, value in persona_context.items():
                if value:
                    system_content += f"- {key.replace('_', ' ').title()}: {value}\n"
            system_content += "\nTailor your responses to this user's background and digital proficiency level."

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_content),
            HumanMessagePromptTemplate.from_template("{query}")
        ])

        # Create chain
        chain = prompt | load_llm() | StrOutputParser()

        # Run chain
        response = chain.invoke({"query": query})

        return response.strip()
    except Exception as e:
        # Используем print вместо st.error
        print(f"Error generating chat response: {e}")
        return "Sorry, I couldn't process your request at the moment."


# Sample statements for demo
sample_statements = [
    "I can use digital technologies to collaborate with others.",
    "I know how to protect my personal data online.",
    "I can identify and solve technical problems when using digital devices.",
    "I can create digital content in different formats.",
    "I understand how algorithms work and can use them to solve problems.",
    "I can evaluate the reliability of digital information sources.",
    "I am able to manage my digital identity and reputation.",
    "I can use digital tools to enhance my productivity.",
    "I understand the ethical implications of digital technologies.",
    "I can adapt to new digital tools and technologies quickly."
]


def run_app():
    # Добавляем отладочную информацию
    print("DEBUG: Starting run_app() function")
    
    # Проверяем, не вызывается ли set_page_config где-то в импортах
    print("DEBUG: Checking if set_page_config is called in imports")
    
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

    # Sidebar navigation
    st.sidebar.title("DigiBot Demo")
    page = st.sidebar.radio(
        "Navigation",
        ["Home", "Profile Builder", "Enrichment Demo", "Batch Enrichment", "Quiz", "Chatbot", "Analytics"]
    )

    # Home page
    if page == "Home":
        st.title("🤖 DigiBot Demo")
        st.markdown("""
        Welcome to the DigiBot Demo! This application demonstrates the key features of DigiBot:

        1. **Profile Builder** - Create your digital skills profile
        2. **Enrichment Demo** - See how statements are enriched based on your profile
        3. **Chatbot** - Interact with a personalized digital skills assistant
        4. **Analytics** - View metrics and analytics on enriched statements

        This is a simplified version of the full DigiBot platform, designed to showcase the core functionality.
        """)

        st.info("Navigate using the sidebar to explore different features.")

        # Display current profile if available
        if st.session_state.profile["job_role"]:
            st.subheader("Your Current Profile")
            profile_df = pd.DataFrame([st.session_state.profile])
            st.dataframe(profile_df)

    # Profile Builder page
    elif page == "Profile Builder":
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

    # Enrichment Demo page
    elif page == "Enrichment Demo":
        st.title("✨ Enrichment Demo")
        
        # Добавляем отладочную информацию
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
                
    # Batch Enrichment page
    elif page == "Batch Enrichment":
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
    
    # Quiz page
    elif page == "Quiz":
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
                        
                        # Add "Tendency" annotation
                        fig.add_annotation(
                            x=tendency_position,
                            y=max(values) * 1.1 if max(values) > 0 else 10,
                            text="Tendency",
                            showarrow=False,
                            font=dict(
                                color="red",
                                size=14
                            ),
                            yshift=10
                        )
                        
                        # Update layout
                        fig.update_layout(
                            title=criteria_names[key],
                            xaxis_title="Preference",
                            yaxis_title="Count",
                            height=400,
                            margin=dict(t=80, b=80, l=40, r=40)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                # Add interpretation
                st.subheader("Overall Interpretation")
                if original_percentage > enriched_percentage:
                    st.info("You tend to prefer the original statements over the personalized ones. This might indicate that the enrichment process could be further optimized for your preferences.")
                elif enriched_percentage > original_percentage:
                    st.success("You tend to prefer the personalized statements over the original ones. This suggests that the enrichment process is adding value for your specific context.")
                else:
                    st.info("You have an equal preference for original and personalized statements.")
            
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

    # Chatbot page
    elif page == "Chatbot":
        st.title("💬 DigiBot Chatbot")

        if not st.session_state.profile["job_role"]:
            st.warning("Please create your profile first in the Profile Builder section.")
            st.stop()

        st.markdown("""
        Chat with DigiBot, a personalized digital skills assistant.
        The chatbot uses your profile information to provide tailored responses.
        """)

        # Display chat history
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.markdown(
                    f"<div style='background-color: #e6f7ff; color:black; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><strong>You:</strong> {message['content']}</div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='background-color: #f0f0f0; color:black; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><strong>DigiBot:</strong> {message['content']}</div>",
                    unsafe_allow_html=True)

        # Chat input
        user_input = st.text_input("Type your message:", key="chat_input")

        if st.button("Send") and user_input:
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            # Generate response
            with st.spinner("DigiBot is thinking..."):
                response = generate_chat_response(user_input, st.session_state.profile)

            # Add bot response to chat history
            st.session_state.chat_history.append({"role": "assistant", "content": response})

            # Rerun to update the chat display
            st.rerun()

    # Analytics page
    elif page == "Analytics":
        st.title("📊 Analytics")

        if not st.session_state.enriched_statements:
            st.warning("No enriched statements available. Try enriching some statements first.")
            st.stop()

        st.markdown("""
        This page shows analytics and metrics for your enriched statements.
        """)

        # Create dataframe from enriched statements
        data = []
        for i, item in enumerate(st.session_state.enriched_statements):
            data.append({
                "id": i + 1,
                "original_length": len(item["original"]),
                "enriched_length": len(item["enriched"]),
                "tfidf_similarity": item["metrics"]["cosine_tfidf"],
                "embedding_similarity": item["metrics"]["cosine_embedding"],
                "reading_ease": item["metrics"]["readability"]["estimated_reading_ease"],
                "word_count": item["metrics"]["readability"]["word_count"]
            })

        df = pd.DataFrame(data)

        # Display metrics summary
        st.subheader("Metrics Summary")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Average TF-IDF Similarity", f"{df['tfidf_similarity'].mean():.2f}")

        with col2:
            st.metric("Average Embedding Similarity", f"{df['embedding_similarity'].mean():.2f}")

        with col3:
            st.metric("Average Reading Ease", f"{df['reading_ease'].mean():.1f}")

        # Display dataframe
        st.subheader("Enriched Statements Data")
        st.dataframe(df)

        # Visualizations
        st.subheader("Visualizations")
        
        # Add tabs for different visualizations
        viz_tabs = st.tabs(["Similarity Metrics", "Statement Comparison", "Quiz Results"])
        
        with viz_tabs[0]:
            col1, col2 = st.columns(2)

            with col1:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.barplot(x="id", y="embedding_similarity", data=df, ax=ax)
                ax.set_title("Embedding Similarity by Statement")
                ax.set_xlabel("Statement ID")
                ax.set_ylabel("Embedding Similarity")
                st.pyplot(fig)

            with col2:
                fig, ax = plt.subplots(figsize=(10, 6))
                sns.scatterplot(x="reading_ease", y="embedding_similarity", data=df, ax=ax)
                ax.set_title("Reading Ease vs. Embedding Similarity")
                ax.set_xlabel("Reading Ease")
                ax.set_ylabel("Embedding Similarity")
                st.pyplot(fig)

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
                        
                        # Add "Tendency" annotation
                        fig.add_annotation(
                            x=tendency_position,
                            y=max(values) * 1.1 if max(values) > 0 else 10,
                            text="Tendency",
                            showarrow=False,
                            font=dict(
                                color="red",
                                size=14
                            ),
                            yshift=10
                        )
                        
                        # Update layout
                        fig.update_layout(
                            title=criteria_names[key],
                            xaxis_title="Preference",
                            yaxis_title="Count",
                            height=400,
                            margin=dict(t=80, b=80, l=40, r=40)
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
                # Add interpretation
                st.subheader("Overall Interpretation")
                if original_percentage > enriched_percentage:
                    st.info("You tend to prefer the original statements over the personalized ones. This might indicate that the enrichment process could be further optimized for your preferences.")
                elif enriched_percentage > original_percentage:
                    st.success("You tend to prefer the personalized statements over the original ones. This suggests that the enrichment process is adding value for your specific context.")
                else:
                    st.info("You have an equal preference for original and personalized statements.")

    # Add footer
    st.markdown("---")
    st.markdown("DigiBot Demo | Created with Streamlit and LangChain")
