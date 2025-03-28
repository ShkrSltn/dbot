import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings

# Load environment variables
load_dotenv()

def load_embedding_model():
    """Loads and returns the embedding model"""
    print("DEBUG: Inside load_embedding_model function")
    try:
        # Use API key from environment variables
        api_key = os.getenv("OPENAI_API_KEY")
        model = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=api_key
        )
        print("DEBUG: OpenAIEmbeddings model loaded successfully")
        return model
    except Exception as e:
        print(f"DEBUG: Error loading embedding model: {e}")
        raise