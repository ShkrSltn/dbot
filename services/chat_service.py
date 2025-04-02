import logging
from typing import Dict, Optional, Any

# LangChain imports
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.ai_service import get_chat_model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_llm(max_tokens: Optional[int] = None):
    """
    Loads and returns the LLM model
    
    Args:
        max_tokens: Maximum number of tokens for the response
        
    Returns:
        Configured LLM model
    """
    logger.info("Loading LLM model")
    try:
        model = get_chat_model(max_tokens=max_tokens)
        logger.info("LLM model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Error loading LLM model: {e}", exc_info=True)
        raise

def generate_chat_response(query: str, persona_context: Dict[str, Any], max_tokens: Optional[int] = None) -> str:
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

        # Get chat model with appropriate settings
        llm = get_chat_model(max_tokens=max_tokens)
            
        # Create and run chain
        chain = prompt | llm | StrOutputParser()
        response = chain.invoke({"query": query})

        return response.strip()
    except Exception as e:
        logger.error(f"Error generating chat response: {e}", exc_info=True)
        return "Sorry, I couldn't process your request at the moment."
