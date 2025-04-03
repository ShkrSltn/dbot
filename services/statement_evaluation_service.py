import logging
import re
from typing import Dict, List, Tuple, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from services.ai_service import get_chat_model
from services.enrichment_service import enrich_statement_with_llm, DEFAULT_PROMPT, BASIC_PROMPT, DIGCOMP_FEW_SHOT_PROMPT, GENERAL_FEW_SHOT_PROMPT
from services.metrics_service import calculate_quality_metrics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Evaluation prompt
EVALUATION_PROMPT = """You are an expert evaluator of digital skills statements.

ORIGINAL STATEMENT:
{original_statement}

ENRICHED STATEMENT:
{enriched_statement}

TASK:
Evaluate the enriched statement based on the following criteria:
1. Clarity (0-5): How clear and understandable is the statement?
2. Relevance for context (0-5): How relevant is the statement to the professional context?
3. Retention of original meaning (0-5): How well does it preserve the core meaning of the original statement?
4. Difficulty (0-5): How complex is the language and concepts used?

Provide your evaluation in the following format:
Clarity: [score]
Relevance for context: [score]
Retention of original meaning: [score]
Difficulty: [score]

Brief explanation: [1-2 sentences explaining your evaluation]
"""

def evaluate_statement_with_llm(
    original_statement: str, 
    enriched_statement: str,
    model_name: str = "gpt-4o",
    temperature: float = 0.3
) -> str:
    """
    Evaluates an enriched statement against the original using LLM
    
    Args:
        original_statement: The original statement
        enriched_statement: The enriched statement to evaluate
        model_name: Name of the LLM model to use
        temperature: Temperature setting for the LLM
        
    Returns:
        Evaluation text with scores and explanation
    """
    try:
        prompt = ChatPromptTemplate.from_template(EVALUATION_PROMPT)
        
        # Create and run the chain
        chain = prompt | get_chat_model(model_name, temperature) | StrOutputParser()
        
        evaluation = chain.invoke({
            "original_statement": original_statement,
            "enriched_statement": enriched_statement
        })
        
        logger.info(f"Evaluated statement with result: {evaluation[:100]}...")
        return evaluation.strip()
    except Exception as e:
        logger.error(f"Error evaluating statement: {str(e)}", exc_info=True)
        raise

def extract_scores(evaluation: str) -> Dict[str, int]:
    """
    Extracts numerical scores from evaluation text
    
    Args:
        evaluation: The evaluation text containing scores
        
    Returns:
        Dictionary with extracted scores
    """
    scores = {
        "clarity": 0, 
        "relevance_for_context": 0, 
        "retention_of_original_meaning": 0, 
        "difficulty": 0
    }
    
    patterns = {
        "clarity": r'clarity\s*:\s*(\d)',
        "relevance_for_context": r'relevance for context\s*:\s*(\d)',
        "retention_of_original_meaning": r'(retention of original meaning|original meaning)\s*:\s*(\d)',
        "difficulty": r'difficulty\s*:\s*(\d)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, evaluation, re.IGNORECASE)
        if match:
            # Handle the special case for retention_of_original_meaning which has a capture group
            if key == "retention_of_original_meaning" and match.group(2):
                scores[key] = int(match.group(2))
            elif key != "retention_of_original_meaning" and match.group(1):
                scores[key] = int(match.group(1))

    logger.info(f"Extracted scores: {scores}")
    return scores

def check_difficulty_threshold(proficiency: str, difficulty: int) -> bool:
    """
    Checks if difficulty meets the threshold for the persona's proficiency level
    
    Args:
        proficiency: User's proficiency level (Beginner, Intermediate, Advanced)
        difficulty: Difficulty score from evaluation
        
    Returns:
        Boolean indicating if threshold is met
    """
    thresholds = {
        "Beginner": (1, 2),       # Difficulty between 1 and 2
        "Intermediate": (2, 3),   # Difficulty between 2 and 3
        "Advanced": (3, 5)        # Difficulty between 3 and 5
    }
    
    min_difficulty, max_difficulty = thresholds.get(proficiency, (0, 5))
    result = min_difficulty <= difficulty <= max_difficulty
    
    logger.info(f"Difficulty threshold check for {proficiency} level: {difficulty} is within [{min_difficulty}, {max_difficulty}]: {result}")
    return result

def regenerate_until_threshold(
    context: str, 
    original_statement: str, 
    proficiency: str,
    statement_length: int = 150,
    prompt_template: Optional[str] = None,
    model_name: str = "gpt-4o",
    temperature: float = 0.7,
    max_attempts: Optional[int] = None
) -> Tuple[str, str, str, int, List[Dict[str, Any]]]:
    """
    Regenerates statement until quality thresholds are met
    
    Args:
        context: The context for enrichment
        original_statement: The original statement to enrich
        proficiency: User's proficiency level
        statement_length: Target length for enriched statement
        prompt_template: Custom prompt template to use
        model_name: Name of the LLM model to use
        temperature: Temperature setting for the LLM
        max_attempts: Maximum number of regeneration attempts (overrides settings)
        
    Returns:
        Tuple containing:
        - original_statement: The original statement
        - best_enriched_statement: The best enriched statement
        - best_evaluation: The evaluation of the best statement
        - attempt_count: Number of attempts made
        - enrichment_history: History of all attempts
    """
    attempt_count = 0
    enrichment_history = []
    
    best_score_sum = 0
    best_enriched_statement = None
    best_evaluation = None
    
    # Get global settings
    from services.db.crud._settings import get_global_settings
    from services.db.crud._prompts import get_all_prompts
    
    global_settings = get_global_settings("user_settings")
    
    # Check if evaluation is enabled
    evaluation_enabled = global_settings.get("evaluation_enabled", True) if global_settings else True
    
    # If evaluation is disabled, just do a single enrichment
    if not evaluation_enabled:
        logger.info("Evaluation is disabled, performing single enrichment")
        enriched_statement = enrich_statement_with_llm(
            context=context,
            original_statement=original_statement,
            statement_length=statement_length,
            prompt_template=prompt_template,
            model_name=model_name,
            temperature=temperature
        )
        
        # Calculate quality metrics
        metrics = calculate_quality_metrics(original_statement, enriched_statement)
        
        # Add to history
        enrichment_history.append({
            "metrics": metrics,
            "original_statement": original_statement,
            "enriched_statement": enriched_statement,
            "evaluation": "Evaluation disabled",
            "scores": {"clarity": 0, "relevance_for_context": 0, "retention_of_original_meaning": 0, "difficulty": 0},
            "attempt": 1,
            "score_sum": 0
        })
        
        return original_statement, enriched_statement, "Evaluation disabled", 1, enrichment_history
    
    # Get max attempts from settings if not provided
    if max_attempts is None:
        max_attempts = global_settings.get("evaluation_max_attempts", 5) if global_settings else 5
    
    # If no prompt template provided, use DEFAULT_PROMPT
    if prompt_template is None:
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
    
    while attempt_count < max_attempts:
        attempt_count += 1
        logger.info(f"Enrichment attempt {attempt_count}/{max_attempts}")
        
        try:
            # Enrich statement
            enriched_statement = enrich_statement_with_llm(
                context=context,
                original_statement=original_statement,
                statement_length=statement_length,
                prompt_template=prompt_template,
                model_name=model_name,
                temperature=temperature
            )
            
            # Evaluate enriched statement
            evaluation = evaluate_statement_with_llm(
                original_statement=original_statement,
                enriched_statement=enriched_statement
            )
            
            # Extract scores
            scores = extract_scores(evaluation)
            
            # Calculate quality metrics
            metrics = calculate_quality_metrics(original_statement, enriched_statement)
            
            # Calculate total score for ranking
            score_sum = (
                scores["clarity"] + 
                scores["relevance_for_context"] + 
                scores["retention_of_original_meaning"]
            )
            
            # Add to history
            enrichment_history.append({
                "metrics": metrics,
                "original_statement": original_statement,
                "enriched_statement": enriched_statement,
                "evaluation": evaluation,
                "scores": scores,
                "attempt": attempt_count,
                "score_sum": score_sum
            })
            
            # Check if this is the best statement so far
            if score_sum > best_score_sum:
                best_score_sum = score_sum
                best_enriched_statement = enriched_statement
                best_evaluation = evaluation
            
            # Check thresholds
            if (scores["clarity"] >= 3 and 
                scores["relevance_for_context"] >= 3 and
                scores["retention_of_original_meaning"] >= 3 and
                check_difficulty_threshold(proficiency, scores["difficulty"])):
                
                logger.info(f"Quality thresholds met on attempt {attempt_count}")
                return original_statement, enriched_statement, evaluation, attempt_count, enrichment_history
                
        except Exception as e:
            logger.error(f"Error during regeneration attempt {attempt_count}: {str(e)}", exc_info=True)
            # Continue to next attempt
    
    # If we've reached max attempts without meeting thresholds, return the best one
    logger.warning(f"Reached maximum attempts ({max_attempts}) without meeting all thresholds. Returning best statement.")
    
    if best_enriched_statement is None:
        logger.error("Failed to generate any valid enriched statements")
        return original_statement, original_statement, "Evaluation failed", attempt_count, enrichment_history
        
    return original_statement, best_enriched_statement, best_evaluation, attempt_count, enrichment_history
