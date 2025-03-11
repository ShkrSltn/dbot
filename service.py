import numpy as np
import os
from dotenv import load_dotenv

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# Load environment variables
load_dotenv()

# Sample statements for demo
SAMPLE_STATEMENTS = [
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

# Initialize LangChain models
def load_llm():
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        api_key="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"
    )

def load_embedding_model():
    print("DEBUG: Inside load_embedding_model function")
    try:
        model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key="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"
        )
        print("DEBUG: OpenAIEmbeddings model loaded successfully")
        return model
    except Exception as e:
        print(f"DEBUG: Error loading embedding model: {e}")
        raise

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
        raise

def calculate_quality_metrics(original, enriched):
    """Calculates quality metrics between original and enriched statements"""
    try:
        print("DEBUG: Starting calculate_quality_metrics")
        # Check for empty strings
        if not original or not enriched:
            raise ValueError("Empty string provided for metrics calculation")

        # Embedding similarity using OpenAI embeddings
        print("DEBUG: Loading embedding model")
        embedding_model = load_embedding_model()
        
        # Get embeddings
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
        tfidf_sim = 0.5 + (embedding_sim * 0.5)  # Use embedding_sim as a base
        
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

def generate_chat_response(query, persona_context, max_tokens=None):
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
        llm = load_llm()
        
        # Apply max_tokens parameter if provided
        if max_tokens is not None:
            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=max_tokens,
                api_key="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"
            )
            
        chain = prompt | llm | StrOutputParser()

        # Run chain
        response = chain.invoke({"query": query})

        return response.strip()
    except Exception as e:
        print(f"Error generating chat response: {e}")
        return "Sorry, I couldn't process your request at the moment."

def get_sample_statements():
    """Returns the list of sample statements"""
    return SAMPLE_STATEMENTS