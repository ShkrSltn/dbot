import os
from dotenv import load_dotenv
from functools import lru_cache
import logging
from typing import Optional, Dict, Any

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default model configurations
DEFAULT_CHAT_MODEL = "gpt-4o"
DEFAULT_CHAT_TEMPERATURE = 0.7
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

@lru_cache(maxsize=10)
def get_openai_api_key() -> str:
    """Get OpenAI API key from environment variables with caching"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in environment variables")
        raise ValueError("OpenAI API key is missing")
    return api_key

@lru_cache(maxsize=10)
def get_chat_model(
    model_name: str = DEFAULT_CHAT_MODEL, 
    temperature: float = DEFAULT_CHAT_TEMPERATURE,
    max_tokens: Optional[int] = None,
    **kwargs
) -> ChatOpenAI:
    """Get a configured ChatOpenAI model instance with caching for efficiency"""
    logger.info(f"Loading chat model: {model_name} (temp: {temperature})")
    
    model_params = {
        "model": model_name,
        "temperature": temperature,
        "api_key": get_openai_api_key(),
        **kwargs
    }
    
    if max_tokens is not None:
        model_params["max_tokens"] = max_tokens
        
    return ChatOpenAI(**model_params)

@lru_cache(maxsize=5)
def get_embedding_model(
    model_name: str = DEFAULT_EMBEDDING_MODEL,
    **kwargs
) -> OpenAIEmbeddings:
    """Get a configured OpenAIEmbeddings model instance with caching for efficiency"""
    logger.info(f"Loading embedding model: {model_name}")
    
    model_params = {
        "model": model_name,
        "api_key": get_openai_api_key(),
        **kwargs
    }
    
    return OpenAIEmbeddings(**model_params) 