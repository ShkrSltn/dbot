# services/evaluation_service.py
import logging
import json
from typing import Dict, Any, Optional, List, Tuple

from langchain.prompts import ChatPromptTemplate
from services.ai_service import get_llm_model

logger = logging.getLogger(__name__)

def evaluate_profile_with_ai(profile_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate user profile data with AI and provide suggestions for improvement.
    
    Args:
        profile_data: Dictionary containing user profile information
        
    Returns:
        Dictionary with evaluation results and suggestions
    """
    try:
        # Extract profile fields
        primary_tasks = profile_data.get("primary_tasks", "")
        job_role = profile_data.get("job_role", "")
        job_domain = profile_data.get("job_domain", "")
        years_experience = profile_data.get("years_experience", 0)
        digital_proficiency = profile_data.get("digital_proficiency", 3)
        
        if not primary_tasks or not job_role or not job_domain:
            return {
                "is_good": True,  # Default to true if no data to evaluate
                "feedback": "",
                "suggestion": ""
            }
        
        # Create the evaluation prompt with improved criteria based on completeness, clarity, and credibility
        prompt = ChatPromptTemplate.from_template("""
        You are an expert career coach helping users create effective digital skills profiles.
        
        User information:
        - Job role: {job_role}
        - Job domain: {job_domain}
        - Years of experience: {years_experience}
        - Digital proficiency level: {digital_proficiency}
        - Primary tasks description: {primary_tasks}
        
        Evaluate the profile information with these criteria:
        
        1. Completeness (1-5 scale):
           - Is the job role a real profession or position?
           - Is the job domain a legitimate industry or field?
           - Is the primary tasks description detailed and comprehensive?
           - Does it include sufficient information about digital skills?
        
        2. Clarity (1-5 scale):
           - Is the primary tasks description clear and easy to understand?
           - Are the tasks specific and action-oriented?
           - Is the language precise and professional?
        
        3. Credibility (1-5 scale):
           - Is the primary tasks description relevant to the job role?
           - Does it contain actual work activities?
           - Is the content coherent and not just random text or symbols?
           - Is it appropriate for the stated job role and domain?
        
        4. Provide a suggested improved version of the primary tasks description that:
           - Maintains the user's intent
           - Is more specific and action-oriented
           - Highlights digital skills relevance
           - Is appropriate for their job role and domain
        
        Format your response as a JSON object with these keys:
        - is_good: boolean (true if all criteria score at least 3, false otherwise)
        - feedback: string (constructive feedback highlighting strengths and areas for improvement)
        - suggestion: string (an improved version of the primary tasks description)
        - invalid_fields: array of strings (names of fields that contain invalid or nonsensical input, if any)
        - completeness: integer (1-5 score)
        - clarity: integer (1-5 score)
        - credibility: integer (1-5 score)
        """)
        
        # Get the LLM model
        llm = get_llm_model(temperature=0.2)  # Lower temperature for more consistent responses
        
        # Create the chain and run it
        chain = prompt | llm
        
        # Convert digital_proficiency to text label for better context
        proficiency_labels = {
            1: "Beginner",
            2: "Basic",
            3: "Intermediate", 
            4: "Advanced",
            5: "Expert"
        }
        
        digital_proficiency_label = proficiency_labels.get(
            digital_proficiency if isinstance(digital_proficiency, int) else 3, 
            "Intermediate"
        )
        
        # Execute the chain
        result = chain.invoke({
            "job_role": job_role,
            "job_domain": job_domain,
            "years_experience": years_experience,
            "digital_proficiency": digital_proficiency_label,
            "primary_tasks": primary_tasks
        })
        
        # Parse the result - the model should return JSON
        try:
            # Try to extract JSON from the response
            response_text = result.content
            # Find JSON content (in case the model added extra text)
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                evaluation = json.loads(json_str)
                
                # Determine if the profile is good based on scores
                scores = [
                    evaluation.get("completeness", 0),
                    evaluation.get("clarity", 0),
                    evaluation.get("credibility", 0)
                ]
                
                # Profile is good if all scores are at least 3
                is_good = all(score >= 3 for score in scores)
                evaluation["is_good"] = is_good
                
                # Ensure all expected keys are present
                if "feedback" not in evaluation:
                    evaluation["feedback"] = "Please provide valid information in all fields."
                if "suggestion" not in evaluation:
                    evaluation["suggestion"] = primary_tasks
                if "invalid_fields" not in evaluation:
                    evaluation["invalid_fields"] = []
            else:
                # Fallback if no JSON found
                evaluation = {
                    "is_good": False,
                    "feedback": "Unable to analyze the input properly. Please ensure all fields contain valid information.",
                    "suggestion": primary_tasks,
                    "invalid_fields": []
                }
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            evaluation = {
                "is_good": False,
                "feedback": "Unable to analyze the input properly. Please ensure all fields contain valid information.",
                "suggestion": primary_tasks,
                "invalid_fields": []
            }
        
        return evaluation
        
    except Exception as e:
        logger.error(f"Error evaluating profile with AI: {str(e)}", exc_info=True)
        # Return a safe default
        return {
            "is_good": False,
            "feedback": "An error occurred during evaluation. Please try again.",
            "suggestion": primary_tasks if 'primary_tasks' in locals() else "",
            "invalid_fields": []
        }