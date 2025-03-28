import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

DEFAULT_PROMPT = """Context: {context}
Original Statement: {original_statement}

Enrich the statement while keeping its meaning intact, ensuring clarity, relevance, 
and appropriate difficulty based on the context. Limit the response to a maximum of 
{length} characters without cutting off mid-sentence. 
Don't make phrases which include the job profile ex. 'As a ...' and don't include 
the digital proficiency level."""

def load_llm():
    """Loads and returns the LLM model for enrichment"""
    # Use API key from environment variables
    api_key = os.getenv("OPENAI_API_KEY")
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        api_key=api_key
    )

def enrich_statement_with_llm(context, original_statement, statement_length=150, prompt_template=None):
    """Enriches a statement using LangChain"""
    try:
        # Calculate the character limit
        statement_length_percent = len(original_statement) / 100 * statement_length
        rounded_length = round(statement_length_percent)

        # Use custom prompt template if provided, otherwise use default
        if prompt_template is None:
            prompt_template = DEFAULT_PROMPT

        prompt = ChatPromptTemplate.from_template(prompt_template)

        # Create and run the chain
        chain = prompt | load_llm() | StrOutputParser()
        
        enriched = chain.invoke({
            "context": context,
            "original_statement": original_statement,
            "length": rounded_length
        })

        return enriched.strip()
    except Exception as e:
        print(f"Error enriching statement: {e}")
        raise 