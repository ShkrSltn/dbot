import streamlit as st
import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from dotenv import load_dotenv
import openai
from sentence_transformers import SentenceTransformer
import numpy as np
import textstat

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")


# Initialize SentenceTransformer model
@st.cache_resource
def load_model():
    return SentenceTransformer('all-MiniLM-L6-v2')


model = load_model()

# Set page config
st.set_page_config(
    page_title="DigiBot Demo",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar navigation
st.sidebar.title("DigiBot Demo")
page = st.sidebar.radio(
    "Navigation",
    ["Home", "Profile Builder", "Enrichment Demo", "Chatbot", "Analytics"]
)

# Mock user data
if 'user' not in st.session_state:
    st.session_state.user = {
        "id": 1,
        "username": "demo_user",
        "role": "user"
    }

if 'profile' not in st.session_state:
    st.session_state.profile = {
        "job_role": "",
        "job_domain": "",
        "years_experience": 0,
        "digital_proficiency": "Beginner",
        "primary_tasks": ""
    }

if 'enriched_statements' not in st.session_state:
    st.session_state.enriched_statements = []

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


# Utility functions
def enrich_statement_with_llm(context, original_statement, statement_length=150):
    """Enriches a statement using OpenAI API"""
    try:
        prompt = f"""
        Context: {context}

        Original statement: {original_statement}

        Please enhance this statement to make it more professional and clear.
        Keep the length around {statement_length} characters.
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert in digital competencies."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error enriching statement: {e}")
        return original_statement


def calculate_quality_metrics(original, enriched):
    """Calculates quality metrics between original and enriched statements"""
    try:
        # TF-IDF similarity (mocked)
        tfidf_sim = 0.75

        # Embedding similarity
        embeddings = model.encode([original, enriched])
        embedding_sim = np.dot(embeddings[0], embeddings[1]) / (
                    np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))

        # Readability metrics
        readability = {
            "flesch_reading_ease": textstat.flesch_reading_ease(enriched),
            "flesch_kincaid_grade": textstat.flesch_kincaid_grade(enriched),
            "coleman_liau_index": textstat.coleman_liau_index(enriched),
            "automated_readability_index": textstat.automated_readability_index(enriched)
        }

        return {
            "cosine_tfidf": float(tfidf_sim),
            "cosine_embedding": float(embedding_sim),
            "readability": readability
        }
    except Exception as e:
        st.error(f"Error calculating metrics: {e}")
        return {
            "cosine_tfidf": 0.0,
            "cosine_embedding": 0.0,
            "readability": {}
        }


def generate_chat_response(query, persona_context):
    """Generates a chat response using OpenAI API"""
    try:
        system_message = "You are a helpful digital skills assistant."

        if persona_context:
            system_message += f"\n\nUser context:\n"
            for key, value in persona_context.items():
                if value:
                    system_message += f"- {key.replace('_', ' ').title()}: {value}\n"
            system_message += "\nTailor your responses to this user's background and digital proficiency level."

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": query}
            ],
            temperature=0.7,
            max_tokens=300
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"Error generating chat response: {e}")
        return "Sorry, I couldn't process your request at the moment."


# Sample statements for demo
sample_statements = [
    "I can use digital technologies to collaborate with others.",
    "I know how to protect my personal data online.",
    "I can identify and solve technical problems when using digital devices.",
    "I can create digital content in different formats.",
    "I understand how algorithms work and can use them to solve problems."
]

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

    if not st.session_state.profile["job_role"]:
        st.warning("Please create your profile first in the Profile Builder section.")
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

        if statement_option == "Custom":
            original_statement = st.text_area("Enter your statement:", height=100)
        else:
            original_statement = statement_option

        statement_length = st.slider("Statement Length (characters)", 100, 300, 150)

    with col2:
        st.subheader("Your Profile")
        for key, value in st.session_state.profile.items():
            st.write(f"**{key.replace('_', ' ').title()}:** {value}")

    if st.button("Enrich Statement") and original_statement:
        with st.spinner("Enriching statement..."):
            # Create context from profile
            context = ", ".join(
                [f"{k.replace('_', ' ').title()}: {v}" for k, v in st.session_state.profile.items() if v])

            # Enrich statement
            enriched_statement = enrich_statement_with_llm(context, original_statement, statement_length)

            # Calculate quality metrics
            metrics = calculate_quality_metrics(original_statement, enriched_statement)

            # Save to session state
            st.session_state.enriched_statements.append({
                "original": original_statement,
                "enriched": enriched_statement,
                "metrics": metrics
            })

        # Display results
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
            st.metric("Flesch Reading Ease", f"{metrics['readability']['flesch_reading_ease']:.1f}")

        # Show detailed readability metrics
        with st.expander("Detailed Readability Metrics"):
            readability_df = pd.DataFrame([metrics['readability']])
            st.dataframe(readability_df)

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
                f"<div style='background-color: #e6f7ff; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><strong>You:</strong> {message['content']}</div>",
                unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div style='background-color: #f0f0f0; padding: 10px; border-radius: 5px; margin-bottom: 10px;'><strong>DigiBot:</strong> {message['content']}</div>",
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
        st.experimental_rerun()

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
            "flesch_reading_ease": item["metrics"]["readability"]["flesch_reading_ease"],
            "flesch_kincaid_grade": item["metrics"]["readability"]["flesch_kincaid_grade"]
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
        st.metric("Average Reading Ease", f"{df['flesch_reading_ease'].mean():.1f}")

    # Display dataframe
    st.subheader("Enriched Statements Data")
    st.dataframe(df)

    # Visualizations
    st.subheader("Visualizations")
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
        sns.scatterplot(x="flesch_reading_ease", y="embedding_similarity", data=df, ax=ax)
        ax.set_title("Reading Ease vs. Embedding Similarity")
        ax.set_xlabel("Flesch Reading Ease")
        ax.set_ylabel("Embedding Similarity")
        st.pyplot(fig)

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

# Add footer
st.markdown("---")
st.markdown("DigiBot Demo | Created with Streamlit")