import os
from dotenv import load_dotenv
import streamlit as st

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

def load_llm():
    """Loads and returns the LLM model for chat"""
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        api_key="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"
    )

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
                model="gpt-4o",
                temperature=0.7,
                max_tokens=max_tokens,
                api_key=os.getenv("OPENAI_API_KEY")
            )
            
        chain = prompt | llm | StrOutputParser()

        # Run chain
        response = chain.invoke({"query": query})

        return response.strip()
    except Exception as e:
        print(f"Error generating chat response: {e}")
        return "Sorry, I couldn't process your request at the moment."
