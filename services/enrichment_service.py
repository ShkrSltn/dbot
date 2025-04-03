import logging
from typing import Optional, Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.ai_service import get_chat_model

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DEFAULT_PROMPT = """You are an expert in personalizing digital skills statements for professionals.

CONTEXT:
{context}

TASK:
Transform the following generic digital skills statement into a personalized version that is more relevant, specific, and tailored to the individual's professional context described above.

ORIGINAL STATEMENT:
{original_statement}

Enrich the statement while keeping its meaning intact, ensuring clarity, relevance, 
and appropriate difficulty based on the context. Limit the response to a maximum of 
{length} characters without cutting off mid-sentence. 
Don't make phrases which include the job profile ex. 'As a ...' and don't include 
the digital proficiency level.

"""

def calculate_length(original_statement: str, statement_length: int) -> int:
    """Calculate the appropriate length for the enriched statement"""
    # If statement_length is a percentage
    if statement_length <= 100:
        return max(150, round(len(original_statement) * (1 + statement_length / 100)))
    # If statement_length is an absolute character count
    return statement_length

def enrich_statement_with_llm(
    context: str, 
    original_statement: str, 
    statement_length: int = 150, 
    prompt_template: Optional[str] = None,
    model_name: str = "gpt-4o",
    temperature: float = 0.7,
    additional_params: Optional[Dict[str, Any]] = None
) -> str:
    """
    Enriches a statement using LangChain
    
    Args:
        context: The context for enrichment
        original_statement: The original statement to enrich
        statement_length: Target length (can be percentage or absolute character count)
        prompt_template: Custom prompt template (uses selected prompt from settings if None)
        model_name: Name of the LLM model to use
        temperature: Temperature setting for the LLM
        additional_params: Additional parameters to pass to the prompt
        
    Returns:
        Enriched statement
    """
    try:
        # Calculate the character limit
        rounded_length = calculate_length(original_statement, statement_length)
        
        # If no prompt template provided, get from settings
        if prompt_template is None:
            # Get global settings
            from services.db.crud._settings import get_global_settings
            from services.db.crud._prompts import get_all_prompts
            
            global_settings = get_global_settings("user_settings")
            selected_prompt_id = global_settings.get("selected_prompt_id", 0) if global_settings else 0
            
            # If selected prompt is default (0), use DEFAULT_PROMPT
            if selected_prompt_id == 0:
                prompt_template = DEFAULT_PROMPT
            else:
                # Get the selected prompt from database
                all_prompts = get_all_prompts()
                selected_prompt = None
                for p in all_prompts:
                    if p["id"] == selected_prompt_id:
                        selected_prompt = p
                        break
                
                # Use the selected prompt or default if not found
                prompt_template = selected_prompt["content"] if selected_prompt else DEFAULT_PROMPT
        
        prompt = ChatPromptTemplate.from_template(prompt_template)

        # Prepare parameters for the prompt
        params = {
            "context": context,
            "original_statement": original_statement,
            "length": rounded_length
        }
        
        # Add any additional parameters
        if additional_params:
            params.update(additional_params)

        # Create and run the chain
        chain = prompt | get_chat_model(model_name, temperature) | StrOutputParser()
        
        logger.info(f"Enriching statement of length {len(original_statement)} to target length {rounded_length}")
        enriched = chain.invoke(params)

        return enriched.strip()
    except Exception as e:
        logger.error(f"Error enriching statement: {str(e)}", exc_info=True)
        raise 