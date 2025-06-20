import logging
from services.ai_service import get_embedding_model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_embedding_model():
    """Loads and returns the embedding model"""
    logger.info("Loading embedding model")
    try:
        model = get_embedding_model()
        logger.info("Embedding model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Error loading embedding model: {e}", exc_info=True)
        raise