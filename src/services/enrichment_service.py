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

# Basic Prompt (V1)
BASIC_PROMPT = """Context: {context}
Original Statement: {original_statement}

Enrich the statement while keeping its meaning intact, ensuring clarity, relevance, 
and appropriate difficulty based on the context. Limit the response to a maximum of 
{length} characters without cutting off mid-sentence. 
Don't make phrases which include the job profile ex. 'As a ...' and don't include 
the digital proficiency level.
"""

# Few Shot Prompt related to Digcomp (V2)
DIGCOMP_FEW_SHOT_PROMPT = """Example 1:
Context: Researcher in AI and education, evaluating information and guiding students.
Original Statement: I know that different search engines may give different search results, because they are influenced by commercial factors.
Problematic Enrichment: Aware of the intricacies of search engines, I understand that varying results can be produced due to influences from commercial elements. This knowledge aids in navigating research.
Revised Enrichment: Search engines produce varying results influenced by commercial factors, requiring careful evaluation to ensure research reliability.

Example 2:
Context: Marketing Manager analyzing campaign data to improve performance.
Original Statement: I know which words to use in order to find what I need quickly (e.g., to search online or within a document).
Problematic Enrichment: I am adept at utilizing appropriate terminology and keywords to efficiently search for specific information online or within a document aiding in swift data gathering and analysis for A1 education rese Ch.
Revised Enrichment: Effective use of targeted keywords ensures fast and accurate retrieval of information, essential for optimizing marketing campaigns.

Example 3:
Context: IT Specialist managing large-scale infrastructure systems.
Original Statement: When I use a search engine, I can take advantage of its advanced features.
Problematic Enrichment: When utilizing a search engine, I am adept at leveraging its sophisticated features to optimize research outcomes.
Revised Enrichment: Advanced search features, such as Boolean operators and filters, help streamline troubleshooting and system management tasks.

Example 4:
Context: Content Creator developing engaging multimedia materials.
Original Statement: I know how to find a website I have visited before.
Problematic Enrichment: I possess the expertise to locate previously visited online resources for research purposes.
Revised Enrichment: Bookmarks and browsing history are used to quickly access previously visited websites, saving time during content creation.

Example 5:
Context: Financial Analyst interpreting online reports and news articles.
Original Statement: I know how to differentiate promoted content from other content I find or receive online (e.g., recognizing an advert on social media or search engines).
Problematic Enrichment: Given my advanced digital proficiency, I have the adeptness to discern promoted content from other types of content I encounter online, such as distinguishing an advertisement on social media or search engines.
Revised Enrichment: Promoted content, such as advertisements, is identified and separated from organic information to ensure accurate financial analysis.

Example 6:
Context: Teacher incorporating critical thinking into digital literacy lessons.
Original Statement: I know how to identify the purpose of an online information source (e.g., to inform, influence, entertain, or sell).
Problematic Enrichment: In the context of academic research and teaching, I am adept at distinguishing the intent of digital information sources, such as to inform, persuade, entertain, or sell.
Revised Enrichment: Identifying whether online content aims to inform, influence, entertain, or sell is a key skill for teaching digital literacy effectively.

Example 7:
Context: Legal Advisor reviewing online documents and evidence.
Original Statement: I critically check if the information I find online is reliable.
Problematic Enrichment: I meticulously assess the veracity of online information to ensure its credibility for research and teaching purposes.
Revised Enrichment: Online information is critically reviewed for accuracy and reliability to support sound legal decisions.

Example 8:
Context: Journalist fact-checking sources for news stories.
Original Statement: I know that some information on the Internet is fake.
Problematic Enrichment: I'm aware that the Internet contains inaccurate data, such as deceptive news, which requires critical evaluation.
Revised Enrichment: Misleading or false online information is identified and verified to maintain journalistic integrity.

Example 9:
Context: Software Developer managing secure data storage solutions.
Original Statement: I know about different storage media (e.g., internal or external hard disk, USB memory, pen drive, memory card).
Problematic Enrichment: I am knowledgeable about various data storage devices, such as internal and external hard drives, USB memory sticks, pen drives, and memory cards, which are essential tools in the process of data collection and analysis for research in A1 education.
Revised Enrichment: Data storage devices, such as hard drives and USB memory sticks, are critical for secure and efficient development workflows.

Example 10:
Context: HR Specialist organizing digital employee records.
Original Statement: I know how to organize digital content (e.g., documents, images, videos) using folders or tagging to find them back later.
Problematic Enrichment: I possess the expertise to efficiently categorize and manage digital content such as documents, images, and videos utilizing techniques like folder organization and tagging.
Revised Enrichment: Digital content is structured with folders and tags, ensuring quick access to employee records and improving HR efficiency.

Context: {context}
Original Statement: {original_statement}
Enrich the statement by integrating the context of a {context}. While keeping its meaning intact, ensuring clarity, relevance, and appropriate difficulty based on the context. Avoid verbose or overly complex language. Limit the response to a maximum of {length} characters without cutting off mid-sentence. Do not include phrases like 'As a ...', 'Revised Enrichment:' or explicit digital proficiency levels.
"""

# General Few Shot Prompt (V3)
GENERAL_FEW_SHOT_PROMPT = """Example 1:
Context: A Project Manager using collaborative tools for team efficiency.
Original Statement: I ensure my team can work together effectively using digital tools.
Enriched Statement: I utilize collaborative platforms to streamline team communication and ensure efficient task delegation, fostering a productive work environment.

Example 2:
Context: A Data Scientist analyzing complex datasets for business insights.
Original Statement: I can analyze data to provide useful insights.
Enriched Statement: I use advanced analytics tools to extract actionable insights from large datasets, enabling informed decision-making and strategic planning.

Example 3:
Context: A Teacher integrating technology into classroom learning.
Original Statement: I use technology to make learning easier for my students.
Enriched Statement: I incorporate interactive tools and digital platforms into my teaching methods to make lessons more engaging and accessible for students.

Example 4:
Context: A Freelance Writer using digital tools for content planning and writing.
Original Statement: I use online tools to help me write better.
Enriched Statement: I utilize content planning platforms and grammar-enhancing tools to produce well-structured and engaging written pieces for my clients.

Example 5:
Context: A Small Business Owner expanding their online presence.
Original Statement: I use social media to promote my business.
Enriched Statement: I strategically utilize social media platforms to build brand awareness, connect with customers, and drive business growth.

Context: {context}
Original Statement: {original_statement}
Enrich the statement while keeping its meaning intact, ensuring clarity, relevance, and appropriate difficulty based on the context. Limit the response to a maximum of {length} characters without cutting off mid-sentence. Don't make phrases which include the job profile ex. 'As a ...' and don't include the digital proficiency level or start with Enriched Statement:
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
            
            # If selected prompt is default (0) or one of the built-in prompts (negative IDs)
            if selected_prompt_id == 0:
                prompt_template = DEFAULT_PROMPT
            elif selected_prompt_id == -1:
                prompt_template = BASIC_PROMPT
            elif selected_prompt_id == -2:
                prompt_template = DIGCOMP_FEW_SHOT_PROMPT
            elif selected_prompt_id == -3:
                prompt_template = GENERAL_FEW_SHOT_PROMPT
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